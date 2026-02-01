import pytest

from app import translator


def test_translate_text_unsupported_language_pair():
    with pytest.raises(translator.UnsupportedLanguagePairError):
        translator.translate_text("hello", "en", "es")


def test_translate_text_model_unavailable(monkeypatch):
    monkeypatch.setattr(translator, "_model", None)
    monkeypatch.setattr(translator, "_tokenizer", None)

    with pytest.raises(translator.ModelUnavailableError):
        translator.translate_text("hello", "en", "fr")
