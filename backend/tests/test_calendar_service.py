from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.security import encrypt_token
from app.models.user import User
from app.services import calendar_service


def _make_user(**overrides: object) -> User:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "google_id": "google-1",
        "email": "user@example.com",
        "google_access_token": None,
        "google_token_expiry": None,
        "google_refresh_token": None,
    }
    defaults.update(overrides)
    return User(**defaults)


class _FakeUserRepository:
    def __init__(self, user: User) -> None:
        self._user = user
        self.update_calls: list[tuple[str, str, datetime, str | None]] = []

    async def get_by_id(self, _user_id: str) -> User | None:
        return self._user

    async def update_google_tokens(
        self,
        user_id: str,
        encrypted_access_token: str,
        expiry: datetime,
        encrypted_refresh_token: str | None = None,
    ) -> None:
        self.update_calls.append((user_id, encrypted_access_token, expiry, encrypted_refresh_token))
        self._user.google_access_token = encrypted_access_token
        self._user.google_token_expiry = expiry


class _FakeCalendarEventRepository:
    def __init__(self) -> None:
        self.created: list[SimpleNamespace] = []

    async def create(
        self,
        user_id: str,
        google_event_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
    ) -> SimpleNamespace:
        event = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            google_event_id=google_event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
        )
        self.created.append(event)
        return event


async def test_ensure_valid_access_token_returns_cached_token_when_not_expired() -> None:
    user = _make_user(
        google_access_token=encrypt_token("cached-access-token"),
        google_token_expiry=datetime.now(UTC) + timedelta(minutes=30),
    )
    user_repo = _FakeUserRepository(user)

    token = await calendar_service._ensure_valid_access_token(user, user_repo)  # type: ignore[arg-type]

    assert token == "cached-access-token"
    assert user_repo.update_calls == []


async def test_ensure_valid_access_token_refreshes_when_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user(
        google_access_token=encrypt_token("stale-access-token"),
        google_token_expiry=datetime.now(UTC) - timedelta(minutes=5),
        google_refresh_token=encrypt_token("refresh-token-value"),
    )
    user_repo = _FakeUserRepository(user)

    async def fake_refresh(refresh_token: str) -> tuple[str, datetime]:
        assert refresh_token == "refresh-token-value"
        return "new-access-token", datetime.now(UTC) + timedelta(hours=1)

    monkeypatch.setattr(calendar_service, "_refresh_google_access_token", fake_refresh)

    token = await calendar_service._ensure_valid_access_token(user, user_repo)  # type: ignore[arg-type]

    assert token == "new-access-token"
    assert len(user_repo.update_calls) == 1


async def test_ensure_valid_access_token_raises_without_refresh_token() -> None:
    user = _make_user()
    user_repo = _FakeUserRepository(user)

    with pytest.raises(calendar_service.CalendarNotConnectedError):
        await calendar_service._ensure_valid_access_token(user, user_repo)  # type: ignore[arg-type]


async def test_create_event_persists_google_event_id(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user(
        google_access_token=encrypt_token("cached-access-token"),
        google_token_expiry=datetime.now(UTC) + timedelta(minutes=30),
    )
    user_repo = _FakeUserRepository(user)
    calendar_repo = _FakeCalendarEventRepository()

    async def fake_post(access_token: str, payload: dict[str, object]) -> dict[str, object]:
        assert access_token == "cached-access-token"
        assert payload["summary"] == "Team sync"
        return {"id": "google-event-abc"}

    monkeypatch.setattr(calendar_service, "_post_calendar_event", fake_post)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=1)
    event = await calendar_service.create_event(
        user_id=str(user.id),
        title="Team sync",
        start=start,
        end=end,
        calendar_repo=calendar_repo,  # type: ignore[arg-type]
        user_repo=user_repo,  # type: ignore[arg-type]
    )

    assert event.google_event_id == "google-event-abc"
    assert calendar_repo.created[0].title == "Team sync"


async def test_create_event_includes_attendees_when_given(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user(
        google_access_token=encrypt_token("cached-access-token"),
        google_token_expiry=datetime.now(UTC) + timedelta(minutes=30),
    )
    user_repo = _FakeUserRepository(user)
    calendar_repo = _FakeCalendarEventRepository()

    async def fake_post(_access_token: str, payload: dict[str, object]) -> dict[str, object]:
        assert payload["attendees"] == [{"email": "a@example.com"}, {"email": "b@example.com"}]
        return {"id": "google-event-xyz"}

    monkeypatch.setattr(calendar_service, "_post_calendar_event", fake_post)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=1)
    await calendar_service.create_event(
        user_id=str(user.id),
        title="Planning",
        start=start,
        end=end,
        calendar_repo=calendar_repo,  # type: ignore[arg-type]
        user_repo=user_repo,  # type: ignore[arg-type]
        attendee_emails=["a@example.com", "b@example.com"],
    )


async def test_create_event_omits_attendees_key_when_none_given(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user(
        google_access_token=encrypt_token("cached-access-token"),
        google_token_expiry=datetime.now(UTC) + timedelta(minutes=30),
    )
    user_repo = _FakeUserRepository(user)
    calendar_repo = _FakeCalendarEventRepository()

    async def fake_post(_access_token: str, payload: dict[str, object]) -> dict[str, object]:
        assert "attendees" not in payload
        return {"id": "google-event-no-attendees"}

    monkeypatch.setattr(calendar_service, "_post_calendar_event", fake_post)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=1)
    await calendar_service.create_event(
        user_id=str(user.id),
        title="Solo focus block",
        start=start,
        end=end,
        calendar_repo=calendar_repo,  # type: ignore[arg-type]
        user_repo=user_repo,  # type: ignore[arg-type]
    )
