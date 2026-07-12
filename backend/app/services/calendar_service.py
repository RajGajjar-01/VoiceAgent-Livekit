from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token
from app.models.calendar_event import CalendarEvent
from app.models.user import User
from app.repositories.calendar_event_repository import CalendarEventRepository
from app.repositories.user_repository import UserRepository

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
_EXPIRY_SKEW_SECONDS = 60


class CalendarNotConnectedError(Exception):
    """Raised when the user has no stored Google refresh token — either they
    never granted the calendar.events scope, or Google revoked it."""


async def _refresh_google_access_token(refresh_token: str) -> tuple[str, datetime]:
    """Same raw-httpx call style as auth_service.complete_google_login —
    this repo doesn't use google-api-python-client anywhere."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    resp.raise_for_status()
    data = resp.json()
    expiry = datetime.now(UTC) + timedelta(seconds=data["expires_in"])
    return str(data["access_token"]), expiry


async def _ensure_valid_access_token(user: User, user_repo: UserRepository) -> str:
    now = datetime.now(UTC)
    if (
        user.google_access_token is not None
        and user.google_token_expiry is not None
        and user.google_token_expiry > now + timedelta(seconds=_EXPIRY_SKEW_SECONDS)
    ):
        return decrypt_token(user.google_access_token)

    if user.google_refresh_token is None:
        raise CalendarNotConnectedError(f"User {user.id} has no stored Google refresh token")

    refresh_token = decrypt_token(user.google_refresh_token)
    access_token, expiry = await _refresh_google_access_token(refresh_token)
    await user_repo.update_google_tokens(
        user_id=str(user.id),
        encrypted_access_token=encrypt_token(access_token),
        expiry=expiry,
    )
    return access_token


async def _post_calendar_event(access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Isolated as its own function so tests can monkeypatch this one call
    wholesale, mirroring the verify_oauth2_token boundary-patch convention
    already used in test_security.py."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _CALENDAR_EVENTS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
        )
    resp.raise_for_status()
    return dict(resp.json())


async def create_event(
    user_id: str,
    title: str,
    start: datetime,
    end: datetime,
    calendar_repo: CalendarEventRepository,
    user_repo: UserRepository,
    attendee_emails: list[str] | None = None,
) -> CalendarEvent:
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    access_token = await _ensure_valid_access_token(user, user_repo)
    payload: dict[str, Any] = {
        "summary": title,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    if attendee_emails:
        payload["attendees"] = [{"email": email} for email in attendee_emails]
    event = await _post_calendar_event(access_token, payload)
    response_attendees = [a["email"] for a in event.get("attendees", []) if "email" in a]
    return await calendar_repo.create(
        user_id=user_id,
        google_event_id=str(event["id"]),
        title=title,
        start_time=start,
        end_time=end,
        html_link=event.get("htmlLink"),
        attendees=response_attendees or None,
    )
