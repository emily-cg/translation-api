from typing import Optional

from pydantic import BaseModel, Field, constr


class TranslationRequest(BaseModel):
    text: constr(min_length=1, max_length=2000)
    source_lang: str = "en"
    target_lang: str
    request_id: Optional[str] = None


class TranslationResponse(BaseModel):
    translation: str
    model: str
    source_lang: str
    target_lang: str
    latency_ms: int
