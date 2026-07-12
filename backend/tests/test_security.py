import time

import jwt
import pytest
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_token,
    encrypt_token,
    verify_access_token,
    verify_google_id_token,
    verify_refresh_token,
)


def test_create_and_verify_access_token_round_trip() -> None:
    token = create_access_token(user_id="abc-123")
    payload = verify_access_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["type"] == "access"


def test_verify_access_token_rejects_expired_token() -> None:
    expired = jwt.encode(
        {"sub": "abc-123", "type": "access", "exp": int(time.time()) - 10},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(jwt.PyJWTError):
        verify_access_token(expired)


def test_verify_access_token_rejects_bad_signature() -> None:
    token = jwt.encode(
        {"sub": "abc-123", "type": "access", "exp": int(time.time()) + 60}, "wrong-secret", algorithm="HS256"
    )
    with pytest.raises(jwt.PyJWTError):
        verify_access_token(token)


def test_create_and_verify_refresh_token_round_trip() -> None:
    token = create_refresh_token(user_id="abc-123")
    payload = verify_refresh_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["type"] == "refresh"


def test_refresh_token_rejected_by_verify_access_token() -> None:
    token = create_refresh_token(user_id="abc-123")
    with pytest.raises(jwt.InvalidTokenError):
        verify_access_token(token)


def test_access_token_rejected_by_verify_refresh_token() -> None:
    token = create_access_token(user_id="abc-123")
    with pytest.raises(jwt.InvalidTokenError):
        verify_refresh_token(token)


def test_encrypt_decrypt_token_round_trip() -> None:
    encrypted = encrypt_token("google-refresh-token-value")
    assert encrypted != "google-refresh-token-value"
    assert decrypt_token(encrypted) == "google-refresh-token-value"


def test_encrypt_token_works_for_access_tokens_too() -> None:
    encrypted = encrypt_token("google-access-token-value")
    assert decrypt_token(encrypted) == "google-access-token-value"


def test_verify_google_id_token_returns_payload_on_valid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_payload = {"sub": "google-user-1", "email": "user@example.com", "email_verified": True}
    seen: dict[str, object] = {}

    def fake_verify_oauth2_token(id_token_str: str, request: object, audience: str) -> dict[str, object]:
        seen["id_token_str"] = id_token_str
        seen["audience"] = audience
        return fake_payload

    monkeypatch.setattr(google_id_token, "verify_oauth2_token", fake_verify_oauth2_token)

    result = verify_google_id_token("fake-id-token")

    assert result == fake_payload
    assert seen["id_token_str"] == "fake-id-token"
    assert seen["audience"] == settings.GOOGLE_CLIENT_ID


def test_verify_google_id_token_propagates_verification_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_verify_oauth2_token(id_token_str: str, request: object, audience: str) -> dict[str, object]:
        raise ValueError("Token used too late")

    monkeypatch.setattr(google_id_token, "verify_oauth2_token", fake_verify_oauth2_token)

    with pytest.raises(ValueError, match="Token used too late"):
        verify_google_id_token("expired-token")
