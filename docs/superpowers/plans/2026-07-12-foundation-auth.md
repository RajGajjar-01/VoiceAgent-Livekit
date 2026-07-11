# Foundation & Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the FastAPI backend, Postgres schema, Google OAuth login (Google-only, JWT-in-cookie session), and a fresh React/Vite/shadcn frontend shell — the foundation the voice-pipeline and agent-actions sub-projects build on.

**Architecture:** FastAPI backend with a repository pattern over async SQLAlchemy/Postgres; Google OAuth 2.0 Authorization Code flow verified server-side, after which the backend mints its own short-lived JWT stored in an httpOnly cookie (no refresh-token endpoint — single JWT with expiry). React SPA (Vite) talks to the backend over CORS with credentials. All new frontend tooling (Vite, shadcn) is scaffolded fresh via official CLIs — nothing is copy-pasted from the reference project; only its dependency list and structural patterns are reused as a guide.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2.x (async) + asyncpg, Alembic, PostgreSQL 18, Redis (`fastapi-limiter`), `uv`, `ruff`, `mypy --strict`, `pytest` + `pytest-asyncio`. React 19 + Vite + TypeScript, Tailwind v4, shadcn/ui, `zustand`, `axios`, `react-router`.

## Global Constraints

- Work only on the `dev` branch. Never commit to `main`.
- All commits use Conventional Commits format (`feat:`, `fix:`, `chore:`, `test:`, `docs:`).
- Google OAuth only — no email/password auth (per `docs/superpowers/specs/2026-07-12-foundation-auth-design.md`).
- Single JWT (HS256) in an httpOnly, secure cookie — no `/auth/refresh` endpoint.
- `google_refresh_token` must be encrypted at rest (Fernet) and never appear in any API response.
- CORS configured with `allow_credentials=True` and an explicit origin allowlist from the start.
- No copy-pasted files from `/home/rajgajjar04/Learnings/python/fastapi-react-supabase-mini` — scaffold fresh, reuse only as a structural/dependency reference.

---

## File Structure

```
backend/
  app/
    api/v1/
      router.py           # aggregates auth + tasks routers
      auth.py               # /auth/google/login, /auth/google/callback, /auth/logout, /auth/me
      tasks.py               # task CRUD
    core/
      config.py              # pydantic-settings
      database.py             # async engine + session factory + get_db dependency
      security.py              # Google ID token verify, JWT mint/verify, Fernet encrypt/decrypt
      dependencies.py           # get_current_user, get_*_repository
      response.py
      exception_handlers.py
      health.py
      rate_limit.py              # fastapi-limiter init
    models/
      base.py                    # SQLAlchemy declarative base
      user.py
      task.py
      calendar_event.py
    repositories/
      base.py
      user_repository.py
      task_repository.py
      # calendar_event_repository.py deliberately not built here — no
      # endpoint in this sub-project writes calendar events yet; the
      # table exists (Task 3 migration) but its repository belongs to
      # the Agent Actions sub-project, which is what will populate it.
    schemas/
      auth.py
      task.py
    main.py
  alembic/
    env.py
    versions/
  alembic.ini
  tests/
    conftest.py                  # env fixture + shared test-DB session fixture
    test_security.py
    test_auth_callback.py         # mocked google token-exchange integration test
    repositories/
      test_user_repository.py
      test_task_repository.py
  pyproject.toml
  .env.example
  Dockerfile
frontend/
  src/
    lib/api.ts
    stores/useAuthStore.ts
    hooks/useAuth.ts
    components/ProtectedRoute.tsx
    components/DashboardLayout.tsx
    components/AppSidebar.tsx
    pages/Landing.tsx
    pages/Dashboard.tsx
    pages/NotFound.tsx
    App.tsx
    main.tsx
  .env.example
docker-compose.yml
```

---

### Task 1: Backend project scaffold + dev infra

**Files:**
- Create: `backend/pyproject.toml`, `backend/.env.example`, `backend/.gitignore`, `docker-compose.yml`, `.gitignore` (root)

**Interfaces:**
- Produces: a `uv`-managed Python 3.13 project with FastAPI/SQLAlchemy/Alembic/etc. installed, and `docker-compose.yml` providing Postgres 18, pgAdmin, and Redis for local dev.

- [ ] **Step 1: Scaffold the uv project**

```bash
mkdir -p backend/app backend/tests
cd backend
uv init --name backend --python 3.13 --no-readme
```

- [ ] **Step 2: Add runtime and dev dependencies**

```bash
uv add fastapi uvicorn[standard] "sqlalchemy[asyncio]>=2.0" asyncpg alembic \
  pydantic-settings pyjwt cryptography google-auth httpx \
  fastapi-limiter redis python-multipart
uv add --dev pytest pytest-asyncio ruff mypy
```

- [ ] **Step 3: Write `pyproject.toml` tool config**

Append to `backend/pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008"]

[tool.mypy]
strict = true
exclude = ["venv", ".venv"]

[[tool.mypy.overrides]]
module = ["asyncpg", "fastapi_limiter.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 4: Write `backend/.env.example`**

```bash
# Postgres
POSTGRES_USER=voiceagent
POSTGRES_PASSWORD=changethis
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=voiceagent

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=changethis
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# Session / crypto
JWT_SECRET=changethis-to-a-random-64-char-string
JWT_EXPIRY_MINUTES=60
REFRESH_TOKEN_ENCRYPTION_KEY=changethis-fernet-key

# App
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=["http://localhost:5173"]
COOKIE_SECURE=false
```

- [ ] **Step 5: Write root `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_USER: voiceagent
      POSTGRES_PASSWORD: changethis
      POSTGRES_DB: voiceagent
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@voiceagent.local
      PGADMIN_DEFAULT_PASSWORD: changethis
    ports: ["5050:80"]
    depends_on: [postgres]

  redis:
    image: redis:latest
    ports: ["6379:6379"]
    volumes: ["redisdata:/data"]

volumes:
  pgdata:
  redisdata:
```

- [ ] **Step 6: Write root `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.env
node_modules/
dist/
.mypy_cache/
.ruff_cache/
*.egg-info/
```

- [ ] **Step 7: Bring up infra and verify**

```bash
docker compose up -d
docker compose ps
```

Expected: `postgres`, `pgadmin`, `redis` all show `Up`/healthy.

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/.env.example backend/.gitignore \
  docker-compose.yml .gitignore
git commit -m "chore: scaffold backend project and dev infra (postgres, pgadmin, redis)"
```

---

### Task 2: Config, database engine, and SQLAlchemy models

**Files:**
- Create: `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/models/__init__.py`, `backend/app/models/base.py`, `backend/app/models/user.py`, `backend/app/models/task.py`, `backend/app/models/calendar_event.py`

**Interfaces:**
- Produces: `settings` (Settings instance), `Base` (declarative base), `get_db` (async generator dependency yielding `AsyncSession`), `User`, `Task`, `CalendarEvent` SQLAlchemy models.

- [ ] **Step 1: Write `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    REDIS_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    JWT_SECRET: str
    JWT_EXPIRY_MINUTES: int = 60
    REFRESH_TOKEN_ENCRYPTION_KEY: str

    FRONTEND_URL: str
    ALLOWED_ORIGINS: list[str]
    COOKIE_SECURE: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
```

- [ ] **Step 2: Write `backend/app/core/database.py`**

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_size=5, max_overflow=10)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
```

- [ ] **Step 3: Write `backend/app/models/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 4: Write `backend/app/models/user.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    google_refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    google_access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    google_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 5: Write `backend/app/models/task.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 6: Write `backend/app/models/calendar_event.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    google_event_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 7: Add `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/models/__init__.py` (empty files)**

```bash
touch backend/app/__init__.py backend/app/core/__init__.py backend/app/models/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/__init__.py backend/app/core/__init__.py backend/app/core/config.py \
  backend/app/core/database.py backend/app/models/
git commit -m "feat: add config, async db engine, and user/task/calendar_event models"
```

---

### Task 3: Alembic setup and initial migration

**Files:**
- Create: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/`

**Interfaces:**
- Consumes: `Base` from `app.models.base`, `settings.database_url` from Task 2.
- Produces: `users`, `tasks`, `calendar_events` tables in Postgres.

- [ ] **Step 1: Init Alembic (async template)**

```bash
cd backend
uv run alembic init -t async alembic
```

- [ ] **Step 2: Edit `backend/alembic.ini`**

Remove the `sqlalchemy.url = ...` line entirely (it will be set from `settings` in `env.py`).

- [ ] **Step 3: Edit `backend/alembic/env.py`**

Replace the `target_metadata = None` line and the URL-loading logic:

```python
# near the top, after existing imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models import user, task, calendar_event  # noqa: E402, F401

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

- [ ] **Step 4: Generate the initial migration**

```bash
uv run alembic revision --autogenerate -m "create users, tasks, calendar_events tables"
```

Expected: a new file in `backend/alembic/versions/` with `create_table` ops for all three tables.

- [ ] **Step 5: Apply the migration and verify**

```bash
uv run alembic upgrade head
docker exec -it $(docker compose ps -q postgres) psql -U voiceagent -d voiceagent -c "\dt"
```

Expected: `users`, `tasks`, `calendar_events`, `alembic_version` tables listed.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add alembic migrations for users, tasks, calendar_events"
```

---

### Task 4: Security module — Google ID token verification, JWT, refresh-token encryption

**Files:**
- Create: `backend/app/core/security.py`
- Test: `backend/tests/test_security.py`, `backend/tests/conftest.py`

**Interfaces:**
- Produces: `create_access_token(user_id: str) -> str`, `verify_access_token(token: str) -> dict[str, str]`, `verify_google_id_token(id_token_str: str) -> dict[str, str]`, `encrypt_refresh_token(token: str) -> str`, `decrypt_refresh_token(token: str) -> str`.

- [ ] **Step 1: Write `backend/tests/conftest.py`**

```python
import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "test")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test")
    monkeypatch.setenv("POSTGRES_SERVER", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    monkeypatch.setenv("REFRESH_TOKEN_ENCRYPTION_KEY", "kX9m2vQZ8pL4nR7tY1wB3cF6hJ0sA5dGjKvM8xN2oQw=")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://localhost:5173"]')
```

- [ ] **Step 2: Write the failing tests — `backend/tests/test_security.py`**

```python
import time

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decrypt_refresh_token,
    encrypt_refresh_token,
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


def test_encrypt_decrypt_refresh_token_round_trip() -> None:
    encrypted = encrypt_refresh_token("google-refresh-token-value")
    assert encrypted != "google-refresh-token-value"
    assert decrypt_refresh_token(encrypted) == "google-refresh-token-value"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend
uv run pytest tests/test_security.py -v
```

Expected: `ModuleNotFoundError` / `ImportError` — `app.core.security` doesn't exist yet.

- [ ] **Step 4: Write `backend/app/core/security.py`**

```python
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
    return google_id_token.verify_oauth2_token(
        id_token_str, google_requests.Request(), settings.GOOGLE_CLIENT_ID
    )


def _fernet() -> Fernet:
    return Fernet(settings.REFRESH_TOKEN_ENCRYPTION_KEY.encode())


def encrypt_refresh_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_refresh_token(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_security.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/security.py backend/tests/conftest.py backend/tests/test_security.py
git commit -m "feat: add JWT, google id-token verification, and refresh-token encryption"
```

---

### Task 5: Repository pattern for users and tasks (with tests against a real test DB)

**Files:**
- Create: `backend/app/repositories/__init__.py`, `backend/app/repositories/base.py`, `backend/app/repositories/user_repository.py`, `backend/app/repositories/task_repository.py`
- Modify: `backend/tests/conftest.py` (add shared DB fixtures — also used by Task 7's callback test)
- Test: `backend/tests/repositories/__init__.py`, `backend/tests/repositories/test_user_repository.py`, `backend/tests/repositories/test_task_repository.py`

**Interfaces:**
- Consumes: `User`, `Task` from Task 2; `AsyncSession` from `app.core.database`.
- Produces: `UserRepository.upsert_from_google(google_id, email, name, avatar_url, encrypted_refresh_token) -> User`, `UserRepository.get_by_id(user_id) -> User | None`, `UserRepository.get_by_google_id(google_id) -> User | None`; `TaskRepository.create(user_id, title) -> Task`, `TaskRepository.list_for_user(user_id) -> list[Task]`, `TaskRepository.mark_done(task_id, user_id) -> Task | None`; a `db_session` pytest fixture usable by any test in `backend/tests/` (not just `repositories/`).

- [ ] **Step 1: Add DB fixtures to `backend/tests/conftest.py`** (append to the file created in Task 4 — creates a throwaway test DB, tables, and a per-test rollback transaction)

```python
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base

TEST_DB_URL = "postgresql+asyncpg://voiceagent:changethis@localhost:5432/voiceagent_test"


@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncGenerator[AsyncSession]:
    connection = await _engine.connect()
    transaction = await connection.begin()
    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()
```

This fixture lives in the top-level `backend/tests/conftest.py` (not a nested `tests/repositories/conftest.py`) specifically so Task 7's `test_auth_callback.py` can reuse it too — pytest fixtures in a parent `conftest.py` are visible to all test files below it.

Note: requires a `voiceagent_test` database. Create it once:

```bash
docker exec -it $(docker compose ps -q postgres) psql -U voiceagent -d voiceagent -c "CREATE DATABASE voiceagent_test;"
```

- [ ] **Step 2: Write the failing tests — `backend/tests/repositories/test_user_repository.py`**

```python
import pytest

from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_upsert_from_google_creates_new_user(db_session) -> None:
    repo = UserRepository(db_session)
    user = await repo.upsert_from_google(
        google_id="g-123", email="a@example.com", name="Alice", avatar_url=None, encrypted_refresh_token="enc"
    )
    assert user.google_id == "g-123"
    assert user.email == "a@example.com"


@pytest.mark.asyncio
async def test_upsert_from_google_updates_existing_user(db_session) -> None:
    repo = UserRepository(db_session)
    first = await repo.upsert_from_google(
        google_id="g-123", email="a@example.com", name="Alice", avatar_url=None, encrypted_refresh_token="enc-1"
    )
    second = await repo.upsert_from_google(
        google_id="g-123", email="a@example.com", name="Alice B", avatar_url=None, encrypted_refresh_token="enc-2"
    )
    assert first.id == second.id
    assert second.name == "Alice B"
    assert second.google_refresh_token == "enc-2"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(db_session) -> None:
    repo = UserRepository(db_session)
    assert await repo.get_by_id("00000000-0000-0000-0000-000000000000") is None
```

- [ ] **Step 3: Write the failing tests — `backend/tests/repositories/test_task_repository.py`**

```python
import pytest

from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_and_list_tasks_for_user(db_session) -> None:
    user = await UserRepository(db_session).upsert_from_google(
        google_id="g-1", email="a@example.com", name="A", avatar_url=None, encrypted_refresh_token="enc"
    )
    repo = TaskRepository(db_session)
    await repo.create(user_id=str(user.id), title="Buy milk")
    tasks = await repo.list_for_user(str(user.id))
    assert len(tasks) == 1
    assert tasks[0].title == "Buy milk"
    assert tasks[0].done is False


@pytest.mark.asyncio
async def test_mark_done_only_affects_owning_user(db_session) -> None:
    user_repo = UserRepository(db_session)
    owner = await user_repo.upsert_from_google(
        google_id="g-1", email="a@example.com", name="A", avatar_url=None, encrypted_refresh_token="enc"
    )
    other = await user_repo.upsert_from_google(
        google_id="g-2", email="b@example.com", name="B", avatar_url=None, encrypted_refresh_token="enc"
    )
    repo = TaskRepository(db_session)
    task = await repo.create(user_id=str(owner.id), title="Buy milk")

    result = await repo.mark_done(str(task.id), user_id=str(other.id))
    assert result is None

    result = await repo.mark_done(str(task.id), user_id=str(owner.id))
    assert result is not None
    assert result.done is True
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
touch backend/tests/repositories/__init__.py
cd backend
uv run pytest tests/repositories/ -v
```

Expected: `ImportError` — repositories don't exist yet.

- [ ] **Step 5: Write `backend/app/repositories/base.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
```

- [ ] **Step 6: Write `backend/app/repositories/user_repository.py`**

```python
from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: str) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def upsert_from_google(
        self,
        google_id: str,
        email: str,
        name: str | None,
        avatar_url: str | None,
        encrypted_refresh_token: str | None,
    ) -> User:
        user = await self.get_by_google_id(google_id)
        if user is None:
            user = User(google_id=google_id, email=email)
            self._session.add(user)

        user.email = email
        user.name = name
        user.avatar_url = avatar_url
        if encrypted_refresh_token is not None:
            user.google_refresh_token = encrypted_refresh_token

        await self._session.commit()
        await self._session.refresh(user)
        return user
```

- [ ] **Step 7: Write `backend/app/repositories/task_repository.py`**

```python
from sqlalchemy import select

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    async def create(self, user_id: str, title: str) -> Task:
        task = Task(user_id=user_id, title=title)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def list_for_user(self, user_id: str) -> list[Task]:
        result = await self._session.execute(
            select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_done(self, task_id: str, user_id: str) -> Task | None:
        task = await self._session.get(Task, task_id)
        if task is None or str(task.user_id) != user_id:
            return None
        task.done = True
        await self._session.commit()
        await self._session.refresh(task)
        return task
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
touch backend/app/repositories/__init__.py
uv run pytest tests/repositories/ -v
```

Expected: 5 passed.

- [ ] **Step 9: Commit**

```bash
git add backend/app/repositories/ backend/tests/repositories/ backend/tests/conftest.py
git commit -m "feat: add user and task repositories with tests"
```

---

### Task 6: Response helpers, exception handlers, and DI dependencies

**Files:**
- Create: `backend/app/core/response.py`, `backend/app/core/exception_handlers.py`, `backend/app/core/dependencies.py`, `backend/app/core/health.py`

**Interfaces:**
- Consumes: `verify_access_token` (Task 4), `UserRepository`/`TaskRepository` (Task 5), `get_db` (Task 2).
- Produces: `success_response`, `error_response`, `get_current_user_id(request) -> str` dependency, `get_user_repository`, `get_task_repository` dependencies, exception handlers, `/live` and `/health` routes.

- [ ] **Step 1: Write `backend/app/core/response.py`**

```python
from typing import Any

from fastapi.responses import JSONResponse


def success_response(data: Any, meta: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data, "meta": meta})


def error_response(status_code: int, title: str, detail: str, error_type: str = "about:blank") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"type": error_type, "title": title, "status": status_code, "detail": detail}, "meta": None},
    )
```

- [ ] **Step 2: Write `backend/app/core/exception_handlers.py`**

```python
import sys
import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import error_response


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return error_response(
            status_code=exc.status_code,
            title=exc.detail.get("title", str(exc.status_code)),
            detail=exc.detail.get("detail", str(exc.detail)),
            error_type=exc.detail.get("type", "about:blank"),
        )
    return error_response(status_code=exc.status_code, title=str(exc.status_code), detail=str(exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "about:blank",
                "title": "VALIDATION_ERROR",
                "status": 422,
                "detail": "Request validation failed",
                "details": exc.errors(),
            },
            "meta": None,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    traceback.print_exc(file=sys.stderr)
    return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal server error")
```

- [ ] **Step 3: Write `backend/app/core/dependencies.py`**

```python
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


async def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "NOT_AUTHENTICATED", "detail": "Not authenticated"},
        )
    try:
        payload = verify_access_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"title": "TOKEN_EXPIRED", "detail": "Invalid or expired session"},
        )
    return str(payload["sub"])


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[UserRepository]:
    yield UserRepository(db)


async def get_task_repository(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[TaskRepository]:
    yield TaskRepository(db)
```

- [ ] **Step 4: Write `backend/app/core/health.py`**

```python
from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.core.response import success_response

router = APIRouter(tags=["health"])


@router.get("/live")
async def liveness():
    return success_response({"status": "alive"})


@router.get("/health")
async def readiness():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return success_response({"status": "healthy"})
    except Exception as e:
        return success_response({"status": "unhealthy", "error": str(e)}, status_code=503)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/response.py backend/app/core/exception_handlers.py \
  backend/app/core/dependencies.py backend/app/core/health.py
git commit -m "feat: add response helpers, exception handlers, DI dependencies, health checks"
```

---

### Task 7: Google OAuth endpoints (login, callback, logout, me)

**Files:**
- Create: `backend/app/schemas/__init__.py`, `backend/app/schemas/auth.py`, `backend/app/api/__init__.py`, `backend/app/api/v1/__init__.py`, `backend/app/api/v1/auth.py`, `backend/app/api/v1/router.py`

**Interfaces:**
- Consumes: `verify_google_id_token`, `create_access_token`, `encrypt_refresh_token` (Task 4); `UserRepository` (Task 5); `get_current_user_id`, `get_user_repository` (Task 6).
- Produces: `router` (APIRouter) mounted under `/api/v1/auth` via `api_router` (Task 8 adds tasks routes to the same router; Task 9 mounts `api_router` in `main.py`).

- [ ] **Step 1: Write `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None
```

- [ ] **Step 2: Write `backend/app/api/v1/auth.py`**

```python
import secrets
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_user_repository
from app.core.security import create_access_token, encrypt_refresh_token, verify_google_id_token
from app.core.response import error_response, success_response
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserProfileResponse

router = APIRouter(tags=["auth"])

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"


def _samesite() -> Literal["lax", "none"]:
    return "none" if settings.COOKIE_SECURE else "lax"


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    resp = RedirectResponse(f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")
    resp.set_cookie("oauth_state", state, httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite(), max_age=600)
    return resp


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    user_repo: UserRepository = Depends(get_user_repository),
) -> RedirectResponse:
    if error is not None:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=consent_denied")

    expected_state = request.cookies.get("oauth_state")
    if not state or state != expected_state:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=invalid_state")

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

    if token_resp.status_code != 200:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

    tokens = token_resp.json()
    id_payload = verify_google_id_token(tokens["id_token"])

    refresh_token = tokens.get("refresh_token")
    encrypted_refresh_token = encrypt_refresh_token(refresh_token) if refresh_token else None

    user = await user_repo.upsert_from_google(
        google_id=id_payload["sub"],
        email=id_payload["email"],
        name=id_payload.get("name"),
        avatar_url=id_payload.get("picture"),
        encrypted_refresh_token=encrypted_refresh_token,
    )

    jwt_token = create_access_token(user_id=str(user.id))
    resp = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard")
    resp.set_cookie(
        "access_token",
        jwt_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        max_age=settings.JWT_EXPIRY_MINUTES * 60,
    )
    resp.delete_cookie("oauth_state")
    return resp


@router.post("/logout")
async def logout() -> Response:
    resp = success_response({"message": "Logged out"})
    resp.delete_cookie("access_token", httponly=True, secure=settings.COOKIE_SECURE, samesite=_samesite())
    return resp


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = await user_repo.get_by_id(user_id)
    if user is None:
        return error_response(404, "USER_NOT_FOUND", "User not found")
    return success_response(
        UserProfileResponse(id=str(user.id), email=user.email, name=user.name, avatar_url=user.avatar_url).model_dump()
    )
```

- [ ] **Step 3: Write `backend/app/api/v1/router.py`**

```python
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth")
```

- [ ] **Step 4: Add `__init__.py` files**

```bash
touch backend/app/schemas/__init__.py backend/app/api/__init__.py backend/app/api/v1/__init__.py
```

- [ ] **Step 5: Write the integration test for the callback — `backend/tests/test_auth_callback.py`**

This mocks Google's token endpoint and ID-token verification so the test never makes a real network call, but exercises the real endpoint code, real DB upsert, and real cookie-setting.

```python
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


class _FakeTokenResponse:
    def __init__(self, status_code: int, body: dict) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> dict:
        return self._body


@pytest.mark.asyncio
async def test_google_callback_creates_user_and_sets_session_cookie(db_session) -> None:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    fake_tokens = {"access_token": "fake", "id_token": "fake-id-token", "refresh_token": "fake-refresh"}
    fake_id_payload = {"sub": "g-999", "email": "new@example.com", "name": "New User", "picture": "http://pic"}

    try:
        with (
            patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_FakeTokenResponse(200, fake_tokens))),
            patch("app.api.v1.auth.verify_google_id_token", return_value=fake_id_payload),
        ):
            with TestClient(app) as client:
                client.cookies.set("oauth_state", "abc")
                resp = client.get(
                    "/api/v1/auth/google/callback",
                    params={"code": "x", "state": "abc"},
                    follow_redirects=False,
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code in (302, 307)
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_google_callback_rejects_mismatched_state(db_session) -> None:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(app) as client:
            client.cookies.set("oauth_state", "expected-state")
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "x", "state": "wrong-state"},
                follow_redirects=False,
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code in (302, 307)
    assert "access_token" not in resp.cookies
    assert "invalid_state" in resp.headers["location"]
```

- [ ] **Step 6: Run the tests**

```bash
cd backend
uv run pytest tests/test_auth_callback.py -v
```

Expected: 2 passed. (Requires `docker compose up -d` running — the app's lifespan connects to the real Redis instance for `FastAPILimiter.init`.)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/ backend/app/api/ backend/tests/test_auth_callback.py
git commit -m "feat: add google oauth login/callback/logout/me endpoints"
```

---

### Task 8: Task CRUD endpoints

**Files:**
- Create: `backend/app/schemas/task.py`, `backend/app/api/v1/tasks.py`
- Modify: `backend/app/api/v1/router.py`

**Interfaces:**
- Consumes: `get_current_user_id`, `get_task_repository` (Task 6); `TaskRepository` (Task 5).
- Produces: `router` mounted under `/api/v1/tasks`.

- [ ] **Step 1: Write `backend/app/schemas/task.py`**

```python
from datetime import datetime

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    title: str


class TaskResponse(BaseModel):
    id: str
    title: str
    done: bool
    created_at: datetime
```

- [ ] **Step 2: Write `backend/app/api/v1/tasks.py`**

```python
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id, get_task_repository
from app.core.response import error_response, success_response
from app.repositories.task_repository import TaskRepository
from app.schemas.task import CreateTaskRequest, TaskResponse

router = APIRouter(tags=["tasks"])


@router.get("")
async def list_tasks(
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
):
    tasks = await task_repo.list_for_user(user_id)
    return success_response(
        [TaskResponse(id=str(t.id), title=t.title, done=t.done, created_at=t.created_at).model_dump() for t in tasks]
    )


@router.post("")
async def create_task(
    body: CreateTaskRequest,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
):
    task = await task_repo.create(user_id=user_id, title=body.title)
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, done=task.done, created_at=task.created_at).model_dump(),
        status_code=201,
    )


@router.patch("/{task_id}/done")
async def mark_task_done(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    task_repo: TaskRepository = Depends(get_task_repository),
):
    task = await task_repo.mark_done(task_id, user_id)
    if task is None:
        return error_response(404, "TASK_NOT_FOUND", "Task not found")
    return success_response(
        TaskResponse(id=str(task.id), title=task.title, done=task.done, created_at=task.created_at).model_dump()
    )
```

- [ ] **Step 3: Wire into the router — modify `backend/app/api/v1/router.py`**

```python
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.tasks import router as tasks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(tasks_router, prefix="/tasks")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/task.py backend/app/api/v1/tasks.py backend/app/api/v1/router.py
git commit -m "feat: add task CRUD endpoints"
```

---

### Task 9: App assembly — CORS, rate limiting, exception handlers, lifespan

**Files:**
- Create: `backend/app/core/rate_limit.py`, `backend/app/main.py`

**Interfaces:**
- Consumes: `api_router` (Task 7/8), `health.router` (Task 6), `settings` (Task 2).
- Produces: the running FastAPI `app`.

- [ ] **Step 1: Write `backend/app/core/rate_limit.py`**

```python
from redis.asyncio import Redis

from app.core.config import settings


def create_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
```

- [ ] **Step 2: Write `backend/app/main.py`**

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.health import router as health_router
from app.core.rate_limit import create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    redis = create_redis_client()
    await FastAPILimiter.init(redis)
    yield
    await FastAPILimiter.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router)
app.include_router(health_router)
```

- [ ] **Step 3: Apply rate limiting to the OAuth callback — modify `backend/app/api/v1/auth.py`**

Add the import and dependency:

```python
from fastapi_limiter.depends import RateLimiter
```

Change the callback route decorator:

```python
@router.get("/google/callback", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def google_callback(
```

- [ ] **Step 4: Run the app and verify it boots**

```bash
cd backend
uv run uvicorn app.main:app --reload
```

In another terminal:

```bash
curl -s http://localhost:8000/live
curl -s http://localhost:8000/health
```

Expected: both return `{"data": {"status": "alive"}, ...}` / `{"data": {"status": "healthy"}, ...}` with HTTP 200.

- [ ] **Step 5: Run the full test suite**

```bash
uv run pytest -v
uv run ruff check .
uv run mypy app
```

Expected: all tests pass, no lint errors, no mypy errors (or only pre-existing/expected ones noted).

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/rate_limit.py backend/app/main.py backend/app/api/v1/auth.py
git commit -m "feat: assemble FastAPI app with CORS, rate limiting, and exception handlers"
```

---

### Task 10: Frontend scaffold — fresh Vite + React + shadcn (no copy-paste)

**Files:**
- Create: `frontend/` (entire fresh Vite scaffold), `frontend/.env.example`

**Interfaces:**
- Produces: a running Vite dev server with Tailwind v4, shadcn/ui initialized, and the specific components this app needs installed.

- [ ] **Step 1: Scaffold the Vite project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
```

- [ ] **Step 2: Install dependencies at latest**

```bash
npm install
npm install axios zustand react-router
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 3: Configure the `@` path alias — modify `frontend/tsconfig.json`**

Add under `compilerOptions`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  }
}
```

- [ ] **Step 4: Configure Vite — write `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

- [ ] **Step 5: Init shadcn/ui and add the components this app needs**

```bash
npx shadcn@latest init -d
npx shadcn@latest add button card sidebar sonner dropdown-menu avatar skeleton
```

Expected: `src/components/ui/` populated with `button.tsx`, `card.tsx`, `sidebar.tsx`, `sonner.tsx`, `dropdown-menu.tsx`, `avatar.tsx`, `skeleton.tsx`, and `src/lib/utils.ts` created with the `cn()` helper.

- [ ] **Step 6: Write `frontend/.env.example`**

```
VITE_API_URL=http://localhost:8000
```

```bash
cp .env.example .env
```

- [ ] **Step 7: Verify the dev server boots**

```bash
npm run dev
```

Expected: Vite prints a local URL (e.g. `http://localhost:5173`); loading it in a browser shows the default Vite+React starter page with no console errors.

- [ ] **Step 8: Commit**

```bash
cd ..
git add frontend/
git commit -m "chore: scaffold frontend with vite, react, tailwind, and shadcn/ui"
```

---

### Task 11: API client and auth store

**Files:**
- Create: `frontend/src/lib/api.ts`, `frontend/src/stores/useAuthStore.ts`, `frontend/src/hooks/useAuth.ts`

**Interfaces:**
- Produces: `api` (configured axios instance), `useAuthStore` (zustand store with `user`, `loading`, `initialize()`, `logout()`), `useAuth()` hook.

- [ ] **Step 1: Write `frontend/src/lib/api.ts`**

```typescript
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})
```

- [ ] **Step 2: Write `frontend/src/stores/useAuthStore.ts`**

```typescript
import { create } from 'zustand'
import { api } from '@/lib/api'

export interface AuthUser {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
}

interface AuthState {
  user: AuthUser | null
  loading: boolean
}

interface AuthActions {
  initialize: () => Promise<void>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  user: null,
  loading: true,

  initialize: async () => {
    set({ loading: true })
    try {
      const res = await api.get<{ data: AuthUser }>('/auth/me')
      set({ user: res.data.data, loading: false })
    } catch {
      set({ user: null, loading: false })
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      set({ user: null, loading: false })
    }
  },
}))
```

- [ ] **Step 3: Write `frontend/src/hooks/useAuth.ts`**

```typescript
import { useAuthStore } from '@/stores/useAuthStore'

export function useAuth() {
  const user = useAuthStore((s) => s.user)
  const loading = useAuthStore((s) => s.loading)
  const initialize = useAuthStore((s) => s.initialize)
  const logout = useAuthStore((s) => s.logout)
  return { user, loading, initialize, logout }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/stores/ frontend/src/hooks/useAuth.ts
git commit -m "feat: add api client and google-only auth store"
```

---

### Task 12: Protected route, layout, and pages

**Files:**
- Create: `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/components/DashboardLayout.tsx`, `frontend/src/pages/Landing.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/NotFound.tsx`

**Interfaces:**
- Consumes: `useAuth()` (Task 11).
- Produces: components used by `App.tsx` routing (Task 13).

- [ ] **Step 1: Write `frontend/src/components/ProtectedRoute.tsx`**

```typescript
import { Navigate, Outlet } from 'react-router'
import { useAuth } from '@/hooks/useAuth'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) return null
  if (!user) return <Navigate to="/" replace />
  return <Outlet />
}
```

- [ ] **Step 2: Write `frontend/src/components/DashboardLayout.tsx`**

```typescript
import { Outlet } from 'react-router'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'

export default function DashboardLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <span className="font-semibold">Voice Agent</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{user?.email}</span>
          <Button variant="outline" size="sm" onClick={() => logout()}>
            Log out
          </Button>
        </div>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 3: Write `frontend/src/pages/Landing.tsx`**

```typescript
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LandingPage() {
  const apiUrl = import.meta.env.VITE_API_URL ?? ''
  const params = new URLSearchParams(window.location.search)
  const error = params.get('error')

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="text-sm text-destructive">
              {error === 'consent_denied' ? 'Google sign-in was cancelled.' : 'Sign-in failed. Please try again.'}
            </p>
          )}
          <Button className="w-full" asChild>
            <a href={`${apiUrl}/api/v1/auth/google/login`}>Continue with Google</a>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 4: Write `frontend/src/pages/Dashboard.tsx`**

```typescript
import { useAuth } from '@/hooks/useAuth'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">
        Welcome{user?.name ? `, ${user.name}` : ''}
      </h1>
      <p className="text-sm text-muted-foreground">Here&apos;s what&apos;s happening.</p>
    </div>
  )
}
```

- [ ] **Step 5: Write `frontend/src/pages/NotFound.tsx`**

```typescript
import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <Button onClick={() => navigate('/', { replace: true })}>Home</Button>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ProtectedRoute.tsx frontend/src/components/DashboardLayout.tsx \
  frontend/src/pages/
git commit -m "feat: add protected route, dashboard layout, and landing/dashboard/404 pages"
```

---

### Task 13: App routing and end-to-end Google OAuth verification

**Files:**
- Modify: `frontend/src/App.tsx`, `frontend/src/main.tsx`

**Interfaces:**
- Consumes: everything from Task 11 and Task 12.
- Produces: the fully wired app, ready for manual end-to-end verification.

- [ ] **Step 1: Write `frontend/src/App.tsx`**

```typescript
import { useEffect } from 'react'
import { Route, Routes } from 'react-router'
import { Toaster } from '@/components/ui/sonner'
import DashboardLayout from '@/components/DashboardLayout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LandingPage from '@/pages/Landing'
import DashboardPage from '@/pages/Dashboard'
import NotFoundPage from '@/pages/NotFound'
import { useAuthStore } from '@/stores/useAuthStore'

export default function App() {
  const initialize = useAuthStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <>
      <Toaster richColors closeButton position="top-right" />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  )
}
```

- [ ] **Step 2: Write `frontend/src/main.tsx`**

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

- [ ] **Step 3: Set up a real Google OAuth client**

In Google Cloud Console: create an OAuth 2.0 Client ID (Web application), add `http://localhost:5173` as an authorized JavaScript origin, and `http://localhost:8000/api/v1/auth/google/callback` as an authorized redirect URI. Enable the Google Calendar API for the project. Put the client ID/secret into `backend/.env`.

- [ ] **Step 4: Run both servers**

```bash
docker compose up -d
cd backend && uv run uvicorn app.main:app --reload &
cd frontend && npm run dev
```

- [ ] **Step 5: Manually verify the full login loop**

1. Open `http://localhost:5173`. Expected: Landing page with "Continue with Google" button.
2. Click it. Expected: redirected to Google's consent screen.
3. Approve. Expected: redirected back to `http://localhost:5173/dashboard`, showing "Welcome, <name>".
4. Refresh the page. Expected: still logged in (session persists via cookie).
5. Click "Log out". Expected: redirected/state clears; navigating to `/dashboard` directly now redirects to `/`.
6. Click "Continue with Google" and cancel on Google's consent screen. Expected: redirected to `/` with a visible "Google sign-in was cancelled" message.
7. In the browser devtools, check the `access_token` cookie: confirm `HttpOnly` and `SameSite=Lax` are set.
8. Query the database directly to confirm the user row was created with a populated (encrypted-looking) `google_refresh_token`:

```bash
docker exec -it $(docker compose ps -q postgres) psql -U voiceagent -d voiceagent \
  -c "SELECT email, name, google_refresh_token IS NOT NULL AS has_refresh_token FROM users;"
```

Expected: one row, `has_refresh_token = t`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: wire app routing and verify end-to-end google oauth login"
```
