from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok(monkeypatch):
    monkeypatch.setattr(main, "is_model_available", lambda: True)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_model_unavailable(monkeypatch):
    monkeypatch.setattr(main, "is_model_available", lambda: False)
    monkeypatch.setattr(main, "model_unavailable_reason", lambda: "model missing")
    response = client.get("/ready")
    assert response.status_code == 500
    assert "Translation model is unavailable." in response.text
