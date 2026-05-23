import logging

from backend.main import app
from fastapi.testclient import TestClient


def test_request_logging_middleware_emits_access_logs(caplog):
    caplog.set_level(logging.INFO, logger="backend.api.middleware.request_logging")
    with TestClient(app) as client:
        client.get("/api/v1/health")
    messages = [r.message for r in caplog.records if r.name == "backend.api.middleware.request_logging"]
    assert any("API request" in m and "/api/v1/health" in m for m in messages)
    assert any("API response" in m and "status=200" in m for m in messages)


def test_request_logging_middleware_logs_post_body(caplog):
    caplog.set_level(logging.INFO, logger="backend.api.middleware.request_logging")
    with TestClient(app) as client:
        client.post("/api/v1/session/ensure")
    messages = [r.message for r in caplog.records if r.name == "backend.api.middleware.request_logging"]
    assert any(
        "API request" in m and "method=POST" in m and "body=-" in m for m in messages
    )

    caplog.clear()
    with TestClient(app) as client:
        client.post(
            "/api/v1/search/",
            json={"keywords": "engineer", "use_llm": False},
        )
    messages = [r.message for r in caplog.records if r.name == "backend.api.middleware.request_logging"]
    assert any(
        "API request" in m and "engineer" in m and "body=" in m for m in messages
    )
