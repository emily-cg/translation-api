import pytest

from app import translator


def test_translate_text_unsupported_language_pair():
    with pytest.raises(translator.UnsupportedLanguagePairError):
        translator.translate_text("hello", "en", "de")


def test_translate_text_model_unavailable(monkeypatch):
    def raise_os_error(*args, **kwargs):
        raise OSError("model missing")

    monkeypatch.setattr(translator, "_load_pair", raise_os_error)
    monkeypatch.setattr(translator, "_MODEL_CACHE", {})

    with pytest.raises(translator.ModelUnavailableError):
        translator.translate_text("hello", "en", "fr")
