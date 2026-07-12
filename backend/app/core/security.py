import time
from typing import Any

import jwt
from cryptography.fernet import Fernet
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings

_ALGORITHM = "HS256"


def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + settings.JWT_EXPIRY_MINUTES * 60}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def verify_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])


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
