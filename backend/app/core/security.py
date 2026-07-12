import time
from typing import Any, Literal

import jwt
from cryptography.fernet import Fernet
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings

_ALGORITHM = "HS256"


def _create_token(user_id: str, token_type: Literal["access", "refresh"], expires_in_seconds: int) -> str:
    payload = {"sub": user_id, "type": token_type, "exp": int(time.time()) + expires_in_seconds}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def _verify_token(token: str, expected_type: Literal["access", "refresh"]) -> dict[str, Any]:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected a {expected_type} token")
    return payload


def create_access_token(user_id: str) -> str:
    return _create_token(user_id, "access", settings.JWT_EXPIRY_MINUTES * 60)


def verify_access_token(token: str) -> dict[str, Any]:
    return _verify_token(token, "access")


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, "refresh", settings.REFRESH_TOKEN_EXPIRY_DAYS * 86400)


def verify_refresh_token(token: str) -> dict[str, Any]:
    return _verify_token(token, "refresh")


def verify_google_id_token(id_token_str: str) -> dict[str, Any]:
    payload: dict[str, Any] = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
        id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
    )
    return payload


def _fernet() -> Fernet:
    return Fernet(settings.REFRESH_TOKEN_ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
