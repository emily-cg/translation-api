import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.logging_utils import TranslateLogSpan, stable_text_hash
from app.middleware import metrics_middleware, request_id_middleware
from app.metrics import (
    translator_errors_total,
    translator_model_available,
)
from app.schemas import TranslationRequest, TranslationResponse
from app.translator import (
    ModelUnavailableError,
    UnsupportedLanguagePairError,
    translator_service,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model is loaded once per worker process (e.g., Uvicorn/Gunicorn workers).
    translator_service.load_all()
    yield


app = FastAPI(lifespan=lifespan)
app.middleware("http")(request_id_middleware)
app.middleware("http")(metrics_middleware)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    available = translator_service.is_available()
    translator_model_available.set(1 if available else 0)
    if not available:
        detail = "Translation model is unavailable."
        reason = translator_service.unavailable_reason()
        if reason:
            detail = f"{detail} {reason}"
        raise HTTPException(status_code=500, detail=detail)
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/supported-languages")
def supported_languages():
    pairs = [
        {"source_lang": src, "target_lang": tgt}
        for src, tgt in translator_service.supported_pairs()
    ]
    return {"pairs": pairs}


@app.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest, request: Request):
    request_id = getattr(request.state, "request_id", None)
    text_length = len(payload.text)
    app_version = os.getenv("APP_VERSION", "unknown")
    text_hash = stable_text_hash(payload.text)
    model_id = (
        translator_service.model_id_for_pair(payload.source_lang, payload.target_lang)
        or "unknown"
    )
    base_fields = {
        "request_id": request_id,
        "source_lang": payload.source_lang,
        "target_lang": payload.target_lang,
        "model_id": model_id,
        "text_length": text_length,
        "app_version": app_version,
        "text_hash": text_hash,
    }

    with TranslateLogSpan(base_fields) as span:
        if payload.source_lang == payload.target_lang:
            translator_errors_total.labels(
                endpoint="/translate", error_category="bad_request"
                ).inc()
            span.failure(status_code=400, error_category="bad_request")
            raise HTTPException(
                status_code=400,
                detail="source_lang and target_lang must be different",
            )

        try:
            translation, model_id = translator_service.translate(
                payload.text,
                payload.source_lang,
                payload.target_lang,
            )
        except UnsupportedLanguagePairError as exc:
            translator_errors_total.labels(
                endpoint="/translate", error_category="bad_request"
            ).inc()
            span.failure(status_code=400, error_category="bad_request")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ModelUnavailableError as exc:
            translator_errors_total.labels(
                endpoint="/translate", error_category="internal_error"
            ).inc()
            span.failure(status_code=500, error_category="internal_error")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            translator_errors_total.labels(
                endpoint="/translate", error_category="internal_error"
            ).inc()
            span.failure(
                status_code=500,
                error_category="internal_error",
                level="exception",
            )
            raise HTTPException(status_code=500, detail="Internal server error") from exc

        latency_ms = span.success(status_code=200)

    return TranslationResponse(
        translation=translation,
        model=model_id,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        latency_ms=latency_ms,
    )
