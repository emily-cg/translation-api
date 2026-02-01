import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_ID = "Helsinki-NLP/opus-mt-en-fr"
_SUPPORTED_PAIRS = {("en", "fr")}

_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
_model.eval()


class UnsupportedLanguagePairError(ValueError):
    pass


class ModelUnavailableError(RuntimeError):
    pass


def _format_supported_pairs() -> str:
    pairs = sorted(f"{src}->{tgt}" for src, tgt in _SUPPORTED_PAIRS)
    return ", ".join(pairs)


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if (source_lang, target_lang) not in _SUPPORTED_PAIRS:
        raise UnsupportedLanguagePairError(
            f"Supported language pairs: {_format_supported_pairs()}"
        )

    try:
        inputs = _tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            outputs = _model.generate(**inputs)
        return _tokenizer.decode(outputs[0], skip_special_tokens=True)
    except OSError as exc:
        raise ModelUnavailableError(
            "Translation model is unavailable. Download the model and try again."
        ) from exc
