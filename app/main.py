import logging
import time
import uuid
import os

from fastapi import FastAPI, HTTPException, Request, Response

from app.logging_utils import TranslateLogSpan
from app.schemas import TranslationRequest, TranslationResponse
from app.translator import (
    MODEL_ID,
    ModelUnavailableError,
    UnsupportedLanguagePairError,
    is_model_available,
    model_unavailable_reason,
    translate_text,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

app = FastAPI()


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not is_model_available():
        detail = "Translation model is unavailable."
        reason = model_unavailable_reason()
        if reason:
            detail = f"{detail} {reason}"
        raise HTTPException(status_code=500, detail=detail)
    return {"status": "ok"}


@app.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest, request: Request):
    request_id = getattr(request.state, "request_id", None)
    text_length = len(payload.text)
    app_version = os.getenv("APP_VERSION", "unknown")
    base_fields = {
        "request_id": request_id,
        "source_lang": payload.source_lang,
        "target_lang": payload.target_lang,
        "model_id": MODEL_ID,
        "text_length": text_length,
        "app_version": app_version,
    }

    with TranslateLogSpan(base_fields) as span:
        if payload.source_lang == payload.target_lang:
            span.failure(status_code=400, error_category="bad_request")
            raise HTTPException(
                status_code=400,
                detail="source_lang and target_lang must be different",
            )

        try:
            translation = translate_text(
                payload.text,
                payload.source_lang,
                payload.target_lang,
            )
        except UnsupportedLanguagePairError as exc:
            span.failure(status_code=400, error_category="bad_request")
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ModelUnavailableError as exc:
            span.failure(status_code=500, error_category="internal_error")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:
            span.failure(
                status_code=500,
                error_category="internal_error",
                level="exception",
            )
            raise HTTPException(status_code=500, detail="Internal server error") from exc

        latency_ms = span.success(status_code=200)

    return TranslationResponse(
        translation=translation,
        model=MODEL_ID,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        latency_ms=latency_ms,
    )
