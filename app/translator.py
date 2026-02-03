from typing import Optional, Any, cast

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_ID = "Helsinki-NLP/opus-mt-en-fr"
_SUPPORTED_PAIRS = {("en", "fr")}

_tokenizer: Optional[Any] = None
_model: Optional[Any] = None
_model_error: Optional[OSError] = None


class UnsupportedLanguagePairError(ValueError):
    pass


class ModelUnavailableError(RuntimeError):
    pass


def load_model() -> None:
    global _tokenizer, _model, _model_error
    try:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
        _model.eval()
        _model_error = None
    except OSError as exc:
        _model_error = exc


def _format_supported_pairs() -> str:
    pairs = sorted(f"{src}->{tgt}" for src, tgt in _SUPPORTED_PAIRS)
    return ", ".join(pairs)


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if (source_lang, target_lang) not in _SUPPORTED_PAIRS:
        raise UnsupportedLanguagePairError(
            f"Supported language pairs: {_format_supported_pairs()}"
        )

    if _model is None or _tokenizer is None:
        raise ModelUnavailableError(
            "Translation model is unavailable. Download the model and try again."
        )

    try:
        inputs = _tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = _model.generate(**inputs)
        return cast(str, _tokenizer.decode(outputs[0], skip_special_tokens=True))
    except OSError as exc:
        raise ModelUnavailableError(
            "Translation model is unavailable. Download the model and try again."
        ) from exc


def is_model_available() -> bool:
    return _model is not None and _tokenizer is not None and _model_error is None


def model_unavailable_reason() -> Optional[str]:
    if _model_error is None:
        return None
    return str(_model_error)
