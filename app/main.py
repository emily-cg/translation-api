import time

from fastapi import FastAPI, HTTPException

from app.schemas import TranslationRequest, TranslationResponse
from app.translator import (
    MODEL_ID,
    ModelUnavailableError,
    UnsupportedLanguagePairError,
    is_model_available,
    model_unavailable_reason,
    translate_text,
)

app = FastAPI()


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
def translate(payload: TranslationRequest):
    if payload.source_lang == payload.target_lang:
        raise HTTPException(
            status_code=400,
            detail="source_lang and target_lang must be different",
        )

    start = time.perf_counter()
    try:
        translation = translate_text(
            payload.text,
            payload.source_lang,
            payload.target_lang,
        )
    except UnsupportedLanguagePairError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    latency_ms = int((time.perf_counter() - start) * 1000)

    return TranslationResponse(
        translation=translation,
        model=MODEL_ID,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        latency_ms=latency_ms,
    )
