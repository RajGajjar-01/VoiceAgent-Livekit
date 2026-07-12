import time

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decrypt_token,
    encrypt_token,
    verify_access_token,
)


def test_create_and_verify_access_token_round_trip() -> None:
    token = create_access_token(user_id="abc-123")
    payload = verify_access_token(token)
    assert payload["sub"] == "abc-123"


def test_verify_access_token_rejects_expired_token() -> None:
    from app.core.config import settings

    expired = jwt.encode(
        {"sub": "abc-123", "exp": int(time.time()) - 10},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        verify_access_token(expired)


def test_verify_access_token_rejects_bad_signature() -> None:
    token = jwt.encode({"sub": "abc-123", "exp": int(time.time()) + 60}, "wrong-secret", algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        verify_access_token(token)


def test_encrypt_decrypt_token_round_trip() -> None:
    encrypted = encrypt_token("google-refresh-token-value")
    assert encrypted != "google-refresh-token-value"
    assert decrypt_token(encrypted) == "google-refresh-token-value"


def test_encrypt_token_works_for_access_tokens_too() -> None:
    encrypted = encrypt_token("google-access-token-value")
    assert decrypt_token(encrypted) == "google-access-token-value"
