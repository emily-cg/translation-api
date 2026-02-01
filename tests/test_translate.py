from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


def test_translate_happy_path(monkeypatch):
    expected_translation = "bonjour"

    def fake_translate(text, source_lang, target_lang):
        return expected_translation

    monkeypatch.setattr(main, "translate_text", fake_translate)
    payload = {
        "text": "hello",
        "source_lang": "en",
        "target_lang": "fr",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["model"] == "Helsinki-NLP/opus-mt-en-fr"
    assert data["source_lang"] == payload["source_lang"]
    assert data["target_lang"] == payload["target_lang"]
    assert data["translation"] == expected_translation
    assert isinstance(data["latency_ms"], int)


def test_translate_missing_target_lang():
    payload = {
        "text": "hello",
        "source_lang": "en",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 422


def test_translate_empty_text():
    payload = {
        "text": "",
        "source_lang": "en",
        "target_lang": "es",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 422


def test_translate_same_source_and_target():
    payload = {
        "text": "hello",
        "source_lang": "en",
        "target_lang": "en",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 400


def test_translate_unsupported_language_pair():
    payload = {
        "text": "hello",
        "source_lang": "en",
        "target_lang": "es",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 400
