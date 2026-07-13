import json
from typing import Any

import pytest
from livekit.agents import APIConnectionError, APIStatusError
from livekit.agents.llm import FallbackAdapter, LLMError

from app.agent import worker
from app.core.config import settings


class _FakeEmitter:
    """Minimal stand-in for rtc.EventEmitter — enough for .on()/.emit()."""

    def __init__(self, label: str) -> None:
        self._label = label
        self._handlers: dict[str, list[Any]] = {}

    @property
    def label(self) -> str:
        return self._label

    def on(self, event: str, handler: Any) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event: str, *args: Any) -> None:
        for handler in self._handlers.get(event, []):
            handler(*args)


def test_is_rate_limit_error_true_for_429() -> None:
    assert worker._is_rate_limit_error(APIStatusError("rate limited", status_code=429)) is True


def test_is_rate_limit_error_false_for_other_status_code() -> None:
    assert worker._is_rate_limit_error(APIStatusError("server error", status_code=500)) is False


def test_is_rate_limit_error_false_for_non_api_error() -> None:
    assert worker._is_rate_limit_error(RuntimeError("boom")) is False


def test_watch_llm_errors_flags_rate_limit_and_clears_on_other_errors() -> None:
    health = worker._LLMHealth()
    llm = _FakeEmitter("test-llm")
    worker._watch_llm_errors(llm, "test", health)  # type: ignore[arg-type]

    llm.emit(
        "error",
        LLMError(
            timestamp=0.0,
            label="test",
            error=APIStatusError("rate limited", status_code=429),
            recoverable=True,
        ),
    )
    assert health.last_error_was_rate_limit is True

    llm.emit(
        "error",
        LLMError(timestamp=0.0, label="test", error=APIConnectionError("boom"), recoverable=False),
    )
    assert health.last_error_was_rate_limit is False


def test_build_llm_returns_bare_primary_without_cloudflare_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CLOUDFLARE_ACCOUNT_ID", None)
    monkeypatch.setattr(settings, "CLOUDFLARE_API_KEY", None)

    llm = worker._build_llm(worker._LLMHealth())

    assert not isinstance(llm, FallbackAdapter)


def test_build_llm_wraps_in_fallback_adapter_with_cloudflare_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CLOUDFLARE_ACCOUNT_ID", "test-account")
    monkeypatch.setattr(settings, "CLOUDFLARE_API_KEY", "test-cf-key")

    llm = worker._build_llm(worker._LLMHealth())

    assert isinstance(llm, FallbackAdapter)
    assert len(llm._llm_instances) == 2


async def test_notify_frontend_publishes_reliable_data_message_on_agent_error_topic() -> None:
    published: dict[str, Any] = {}

    class _FakeLocalParticipant:
        async def publish_data(self, payload: bytes, *, reliable: bool, topic: str) -> None:
            published["payload"] = json.loads(payload.decode("utf-8"))
            published["reliable"] = reliable
            published["topic"] = topic

    class _FakeRoom:
        local_participant = _FakeLocalParticipant()

    class _FakeCtx:
        room = _FakeRoom()

    await worker._notify_frontend(_FakeCtx(), worker.RATE_LIMIT_MESSAGE)  # type: ignore[arg-type]

    assert published == {
        "payload": {"type": "agent_error", "message": worker.RATE_LIMIT_MESSAGE},
        "reliable": True,
        "topic": "agent-error",
    }


async def test_notify_frontend_swallows_publish_failures() -> None:
    class _FakeLocalParticipant:
        async def publish_data(self, *args: Any, **kwargs: Any) -> None:
            raise ConnectionError("room gone")

    class _FakeRoom:
        local_participant = _FakeLocalParticipant()

    class _FakeCtx:
        room = _FakeRoom()

    # Must not raise — a failed notification shouldn't crash the worker.
    await worker._notify_frontend(_FakeCtx(), worker.LLM_UNAVAILABLE_MESSAGE)  # type: ignore[arg-type]
