import os

from fastapi import HTTPException

from app.logging_utils import TranslateLogSpan, stable_text_hash
from app.metrics import translator_errors_total
from app.schemas import TranslationRequest
from app.translator import translator_service


def handle_translate_error(
    span: TranslateLogSpan,
    status_code: int,
    error_category: str,
    detail: str,
    exc: Exception,
) -> None:
    translator_errors_total.labels(
        endpoint="/translate", error_category=error_category
    ).inc()
    level = "exception" if status_code == 500 and error_category == "internal_error" else "info"
    span.failure(status_code=status_code, error_category=error_category, level=level)
    raise HTTPException(status_code=status_code, detail=detail) from exc


def build_base_fields(payload: TranslationRequest, request_id: str | None) -> dict:
    text_length = len(payload.text)
    app_version = os.getenv("APP_VERSION", "unknown")
    text_hash = stable_text_hash(payload.text)
    model_id = (
        translator_service.model_id_for_pair(payload.source_lang, payload.target_lang)
        or "unknown"
    )
    return {
        "request_id": request_id,
        "source_lang": payload.source_lang,
        "target_lang": payload.target_lang,
        "model_id": model_id,
        "text_length": text_length,
        "app_version": app_version,
        "text_hash": text_hash,
    }
