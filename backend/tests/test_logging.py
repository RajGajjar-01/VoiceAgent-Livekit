import json

import pytest
import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logging import add_request_context_middleware, configure_logging


def test_configure_logging_uses_json_renderer_in_production(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    configure_logging()
    structlog.get_logger().info("test_event", foo="bar")

    last_line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(last_line)
    assert payload["event"] == "test_event"
    assert payload["foo"] == "bar"


def test_configure_logging_uses_console_renderer_in_development(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    configure_logging()
    structlog.get_logger().info("test_event", foo="bar")

    last_line = capsys.readouterr().out.strip().splitlines()[-1]
    assert "test_event" in last_line
    with pytest.raises(json.JSONDecodeError):
        json.loads(last_line)


def test_request_context_middleware_binds_request_id_and_clears_after() -> None:
    app = FastAPI()
    add_request_context_middleware(app)

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    with structlog.testing.capture_logs(processors=[structlog.contextvars.merge_contextvars]) as captured:
        response = TestClient(app).get("/ping")

    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    assert request_id

    completed_events = [e for e in captured if e["event"].startswith("request_completed")]
    assert len(completed_events) == 1
    event = completed_events[0]["event"]
    assert event.startswith("request_completed GET /ping 200 ")
    assert event.endswith("ms")
    assert completed_events[0]["request_id"] == request_id

    # contextvars must not leak into whatever runs next on this task/thread
    assert structlog.contextvars.get_contextvars() == {}


def test_request_context_middleware_reuses_incoming_request_id() -> None:
    app = FastAPI()
    add_request_context_middleware(app)

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    response = TestClient(app).get("/ping", headers={"X-Request-ID": "client-supplied-id"})
    assert response.headers["x-request-id"] == "client-supplied-id"
