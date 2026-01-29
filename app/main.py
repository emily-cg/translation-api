import time

from fastapi import FastAPI, HTTPException

from app.schemas import TranslationRequest, TranslationResponse

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"status": "ok"}


@app.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest):
    if payload.source_lang == payload.target_lang:
        raise HTTPException(
            status_code=400,
            detail="source_lang and target_lang must be different",
        )

    start = time.perf_counter()
    translation = f"[stub] {payload.text}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    return TranslationResponse(
        translation=translation,
        model="stub",
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        latency_ms=latency_ms,
    )
