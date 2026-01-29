from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_translate_happy_path():
    payload = {
        "text": "hello",
        "source_lang": "en",
        "target_lang": "es",
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "stub"
    assert data["source_lang"] == payload["source_lang"]
    assert data["target_lang"] == payload["target_lang"]
    assert data["translation"].startswith("[stub] ")
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
