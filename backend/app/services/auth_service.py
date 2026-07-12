from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    encrypt_token,
    verify_google_id_token,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"


def build_authorization_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"


async def complete_google_login(code: str, user_repo: UserRepository) -> tuple[User, str, str]:
    """Exchanges the OAuth code for Google tokens, upserts the user, and
    mints our own access + refresh token pair for the session.

    Returns (user, access_token, refresh_token) — the last two are ours,
    unrelated to Google's own access/refresh tokens, which are encrypted
    and stored on the user row instead of ever being sent to the browser.
    """
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    token_resp.raise_for_status()
    tokens = token_resp.json()

    id_payload = verify_google_id_token(tokens["id_token"])

    google_refresh_token = tokens.get("refresh_token")
    encrypted_google_refresh_token = encrypt_token(google_refresh_token) if google_refresh_token else None

    google_access_token = tokens.get("access_token")
    encrypted_google_access_token = encrypt_token(google_access_token) if google_access_token else None
    expires_in = tokens.get("expires_in")
    google_access_token_expiry = (
        datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in is not None else None
    )

    user = await user_repo.upsert_from_google(
        google_id=id_payload["sub"],
        email=id_payload["email"],
        name=id_payload.get("name"),
        avatar_url=id_payload.get("picture"),
        encrypted_refresh_token=encrypted_google_refresh_token,
        encrypted_access_token=encrypted_google_access_token,
        access_token_expiry=google_access_token_expiry,
    )

    access_token = create_access_token(user_id=str(user.id))
    refresh_token = create_refresh_token(user_id=str(user.id))
    return user, access_token, refresh_token
