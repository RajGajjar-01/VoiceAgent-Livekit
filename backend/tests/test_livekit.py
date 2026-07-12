import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from livekit import api

from app.api.v1.livekit import router as livekit_router
from app.core.dependencies import get_current_user_id, get_user_repository
from app.services import livekit_service


class _FakeGrants:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


class _FakeAccessToken:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.identity: str | None = None
        self.name: str | None = None
        self.metadata: str | None = None
        self.grants: _FakeGrants | None = None

    def with_identity(self, identity: str) -> "_FakeAccessToken":
        self.identity = identity
        return self

    def with_name(self, name: str) -> "_FakeAccessToken":
        self.name = name
        return self

    def with_metadata(self, metadata: str) -> "_FakeAccessToken":
        self.metadata = metadata
        return self

    def with_grants(self, grants: _FakeGrants) -> "_FakeAccessToken":
        self.grants = grants
        return self

    def to_jwt(self) -> str:
        return "fake.jwt.token"


def test_mint_token_grants_room_join_for_deterministic_room(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "AccessToken", _FakeAccessToken)
    monkeypatch.setattr(api, "VideoGrants", _FakeGrants)

    token, room = livekit_service.mint_token("user-123", "user@example.com")

    assert token == "fake.jwt.token"
    assert room == "assistant-user-123"


class _FakeUser:
    def __init__(self, user_id: str, email: str) -> None:
        self.id = user_id
        self.email = email


class _FakeUserRepository:
    def __init__(self, user: _FakeUser | None) -> None:
        self._user = user

    async def get_by_id(self, _user_id: str) -> _FakeUser | None:
        return self._user


def _build_app(user: _FakeUser | None) -> FastAPI:
    app = FastAPI()
    app.include_router(livekit_router, prefix="/api/v1/livekit")
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    app.dependency_overrides[get_user_repository] = lambda: _FakeUserRepository(user)
    return app


def test_create_livekit_token_returns_token_url_and_room(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "AccessToken", _FakeAccessToken)
    monkeypatch.setattr(api, "VideoGrants", _FakeGrants)

    app = _build_app(_FakeUser("user-123", "user@example.com"))
    response = TestClient(app).post("/api/v1/livekit/token")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["token"] == "fake.jwt.token"
    assert body["room"] == "assistant-user-123"
    assert body["url"]


def test_create_livekit_token_404s_when_user_not_found() -> None:
    app = _build_app(None)
    response = TestClient(app).post("/api/v1/livekit/token")

    assert response.status_code == 404
    assert response.json()["error"]["title"] == "USER_NOT_FOUND"
