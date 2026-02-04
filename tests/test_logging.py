import uuid

import pytest
from fastapi.testclient import TestClient

import app.logging_utils as logging_utils
import app.main as main


@pytest.fixture()
def client():
    return TestClient(main.app)


def test_request_id_middleware_echoes_header(client):
    response = client.get("/health", headers={"X-Request-ID": "test-id-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "test-id-123"


def test_request_id_middleware_generates_header(client):
    response = client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    uuid.UUID(request_id)


def test_translate_success_logs(client, monkeypatch):
    payload = {"text": "hello", "source_lang": "en", "target_lang": "fr"}
    log_calls = []

    def fake_log_translate(event, **kwargs):
        log_calls.append((event, kwargs))

    monkeypatch.setattr(
        main.translator_service,
        "translate",
        lambda *args, **kwargs: ("bonjour", "Helsinki-NLP/opus-mt-en-fr"),
    )
    monkeypatch.setattr(logging_utils, "log_translate", fake_log_translate)

    response = client.post(
        "/translate", json=payload, headers={"X-Request-ID": "test-id-123"}
    )

    assert response.status_code == 200
    events = [event for event, _ in log_calls]
    assert "translate_start" in events
    assert "translate_success" in events

    success_call = next(event for event in log_calls if event[0] == "translate_success")
    kwargs = success_call[1]
    assert kwargs["request_id"] == "test-id-123"
    assert kwargs["status_code"] == 200
    assert isinstance(kwargs["latency_ms"], int)
    assert kwargs["latency_ms"] >= 0
    assert "source_lang" in kwargs
    assert "target_lang" in kwargs
    assert "model_id" in kwargs
    assert "text_length" in kwargs
    assert "text_hash" in kwargs


def test_translate_failure_logs(client, monkeypatch):
    payload = {"text": "hello", "source_lang": "en", "target_lang": "en"}
    log_calls = []

    def fake_log_translate(event, **kwargs):
        log_calls.append((event, kwargs))

    monkeypatch.setattr(logging_utils, "log_translate", fake_log_translate)

    response = client.post(
        "/translate", json=payload, headers={"X-Request-ID": "test-id-123"}
    )

    assert response.status_code == 400
    failure_call = next(event for event in log_calls if event[0] == "translate_failure")
    kwargs = failure_call[1]
    assert kwargs["request_id"] == "test-id-123"
    assert kwargs["status_code"] == 400
    assert kwargs["error_category"] == "bad_request"
    assert isinstance(kwargs["latency_ms"], int)
    assert kwargs["latency_ms"] >= 0
    assert "text_hash" in kwargs


def test_stable_text_hash_is_deterministic():
    first = logging_utils.stable_text_hash("hello")
    second = logging_utils.stable_text_hash("hello")
    assert first == second
    assert first != "hello"
