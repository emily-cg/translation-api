from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


def test_metrics_exposes_request_and_latency_metrics():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "translator_requests_total" in body
    assert "translator_request_latency_seconds_bucket" in body


def test_metrics_exposes_error_metrics():
    payload = {"text": "hello", "source_lang": "en", "target_lang": "en"}
    client.post("/translate", json=payload)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "translator_errors_total" in response.text
