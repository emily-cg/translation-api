import pytest

from app import translator


def test_translate_text_unsupported_language_pair():
    with pytest.raises(translator.UnsupportedLanguagePairError):
        translator.translate_text("hello", "en", "es")


def test_translate_text_model_unavailable(monkeypatch):
    def raise_os_error(*args, **kwargs):
        raise OSError("model missing")

    monkeypatch.setattr(translator._model, "generate", raise_os_error)

    with pytest.raises(translator.ModelUnavailableError):
        translator.translate_text("hello", "en", "fr")
