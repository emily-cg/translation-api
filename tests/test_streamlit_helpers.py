from types import SimpleNamespace

import streamlit_app


def test_build_language_options():
    pairs = [
        {"source_lang": "en", "target_lang": "fr"},
        {"source_lang": "en", "target_lang": "es"},
        {"source_lang": "de", "target_lang": "en"},
    ]
    sources, targets = streamlit_app.build_language_options(pairs)
    assert sources == ["de", "en"]
    assert targets["en"] == ["es", "fr"]
    assert targets["de"] == ["en"]


def test_fetch_supported_pairs_cached(monkeypatch):
    dummy_st = SimpleNamespace(session_state={})
    monkeypatch.setattr(streamlit_app, "st", dummy_st)

    calls = {"count": 0}

    class DummyResponse:
        ok = True

        def json(self):
            return {"pairs": [{"source_lang": "en", "target_lang": "fr"}]}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        return DummyResponse()

    monkeypatch.setattr(streamlit_app.requests, "get", fake_get)

    first = streamlit_app.fetch_supported_pairs()
    second = streamlit_app.fetch_supported_pairs()

    assert calls["count"] == 1
    assert first == second == [{"source_lang": "en", "target_lang": "fr"}]
