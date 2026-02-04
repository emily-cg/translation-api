from typing import Optional, Any, cast, Dict, Tuple

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

_SUPPORTED_MODELS: Dict[Tuple[str, str], str] = {
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
}

_MODEL_CACHE: Dict[Tuple[str, str], Tuple[Any, Any]] = {}
_model_error: Optional[OSError] = None


class UnsupportedLanguagePairError(ValueError):
    pass


class ModelUnavailableError(RuntimeError):
    pass


def load_model() -> None:
    global _model_error
    try:
        for pair in _SUPPORTED_MODELS.keys():
            _load_pair(pair)
        _model_error = None
    except OSError as exc:
        _model_error = exc


def _load_pair(pair: Tuple[str, str]) -> None:
    model_id = _SUPPORTED_MODELS[pair]
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    model.eval()
    _MODEL_CACHE[pair] = (tokenizer, model)


def _format_supported_pairs() -> str:
    pairs = sorted(f"{src}->{tgt}" for src, tgt in _SUPPORTED_MODELS.keys())
    return ", ".join(pairs)


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    pair = (source_lang, target_lang)
    if pair not in _SUPPORTED_MODELS:
        raise UnsupportedLanguagePairError(
            f"Supported language pairs: {_format_supported_pairs()}"
        )

    if pair not in _MODEL_CACHE:
        try:
            _load_pair(pair)
        except OSError as exc:
            raise ModelUnavailableError(
                "Translation model is unavailable. Download the model and try again."
            ) from exc

    tokenizer, model = _MODEL_CACHE[pair]
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        outputs = model.generate(**inputs)
    return cast(str, tokenizer.decode(outputs[0], skip_special_tokens=True))


def is_model_available() -> bool:
    return _model_error is None


def model_unavailable_reason() -> Optional[str]:
    if _model_error is None:
        return None
    return str(_model_error)


def model_id_for_pair(source_lang: str, target_lang: str) -> Optional[str]:
    return _SUPPORTED_MODELS.get((source_lang, target_lang))
