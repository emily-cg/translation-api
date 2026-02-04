import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.handlers import build_base_fields, handle_translate_error
from app.logging_utils import TranslateLogSpan
from app.middleware import metrics_middleware, request_id_middleware
from app.metrics import translator_model_available
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
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
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
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/supported-languages")
def supported_languages() -> dict:
    pairs = [
        {"source_lang": src, "target_lang": tgt}
        for src, tgt in translator_service.supported_pairs()
    ]
    return {"pairs": pairs}


@app.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest, request: Request) -> TranslationResponse:
    request_id = getattr(request.state, "request_id", None)
    base_fields = build_base_fields(payload, request_id)

    with TranslateLogSpan(base_fields) as span:
        if payload.source_lang == payload.target_lang:
            handle_translate_error(
                span,
                400,
                "bad_request",
                "source_lang and target_lang must be different",
                ValueError("source_lang == target_lang"),
            )

        try:
            translation, model_id = translator_service.translate(
                payload.text,
                payload.source_lang,
                payload.target_lang,
            )
        except UnsupportedLanguagePairError as exc:
            handle_translate_error(span, 400, "bad_request", str(exc), exc)
        except ModelUnavailableError as exc:
            handle_translate_error(span, 500, "internal_error", str(exc), exc)
        except Exception as exc:
            handle_translate_error(
                span, 500, "internal_error", "Internal server error", exc
            )

        latency_ms = span.success(status_code=200)

    return TranslationResponse(
        translation=translation,
        model=model_id,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        latency_ms=latency_ms,
    )
