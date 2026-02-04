from typing import Optional, Annotated

from pydantic import BaseModel, StringConstraints


class TranslationRequest(BaseModel):
    text: Annotated[
        str,
        StringConstraints(min_length=1, max_length=1000, strip_whitespace=True),
    ]
    source_lang: str = "en"
    target_lang: str
    request_id: Optional[str] = None


class TranslationResponse(BaseModel):
    translation: str
    model: str
    source_lang: str
    target_lang: str
    latency_ms: int
