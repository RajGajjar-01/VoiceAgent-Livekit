# Foundation & Auth — Design

Sub-project 1 of 4 for the Voice-Driven AI Agent hiring task (see `task.md`). Establishes the backend/frontend scaffold, Postgres schema, Google OAuth login, session handling, and dev infra that the later voice-pipeline and agent-actions sub-projects build on.

## 1. Tech Stack

- **Backend:** FastAPI (async), SQLAlchemy (async) + Alembic for migrations, PostgreSQL 18, repository pattern for data access, `uv` for dependency management, `ruff` + `mypy --strict`.
- **Frontend:** React + Vite (SPA). Calls the FastAPI backend via `fetch`/`axios` with `credentials: include`.
- **Auth:** Google OAuth 2.0 (Authorization Code flow). After verifying Google's ID token, the backend mints its own JWT (HS256) and sets it as an httpOnly, secure cookie. No Supabase, no third-party auth provider.
- **Dev infra (docker-compose):** `postgres:18-alpine`, `dpage/pgadmin4:latest`, `redis:latest`.
- **Rate limiting:** `fastapi-limiter` (Redis-backed), applied to `/auth/google/callback` and other sensitive/abusable endpoints.

## 2. Backend Structure

```
backend/
  app/
    api/v1/
      router.py
      auth.py            # /auth/google/login, /auth/google/callback, /auth/logout, /auth/me
      tasks.py            # task CRUD endpoints
    core/
      config.py           # pydantic-settings
      database.py          # async SQLAlchemy engine + session factory + get_db dependency
      dependencies.py      # get_current_user, get_task_repository, etc.
      security.py           # verify Google ID token, mint/verify our own JWT, encrypt/decrypt refresh tokens
      exception_handlers.py
      response.py
    models/
      user.py               # SQLAlchemy model
      task.py
      calendar_event.py      # local audit/log of bookings made via the agent
    repositories/
      base.py
      user_repository.py
      task_repository.py
      calendar_event_repository.py
    schemas/
      auth.py
      task.py
    main.py                   # FastAPI app, lifespan, CORS, routers, exception handlers
  alembic/
    versions/
    env.py
  alembic.ini
  docker-compose.yml
  Dockerfile                    # for later AWS deployment, not local dev
  pyproject.toml
```

## 3. Data Model

- **users**: `id` (uuid pk), `google_id` (unique), `email` (unique), `name`, `avatar_url`, `google_refresh_token` (encrypted at rest), `google_access_token` (nullable, short-lived cache), `google_token_expiry`, `created_at`, `updated_at`.
- **tasks**: `id`, `user_id` (fk), `title`, `done` (bool), `created_at`, `updated_at`.
- **calendar_events**: `id`, `user_id` (fk), `google_event_id`, `title`, `start_time`, `end_time`, `created_at` — a local log of bookings made through the agent. This is **not** the source of truth for "what's on my schedule" reads; those query the Google Calendar API live. It exists so the dashboard can show recent agent actions without re-querying Google, and so we have an audit trail if a booking needs debugging.

The `google_refresh_token` column exists because the LiveKit voice agent runs as a separate background worker outside any HTTP request — it still needs to call the Calendar API on the user's behalf when the user says "book a meeting," so the refresh token must be persisted and retrievable server-side, not just held in the browser session.

## 4. Auth Flow

1. `GET /auth/google/login` → redirects to Google's OAuth consent screen. Scopes: `openid email profile https://www.googleapis.com/auth/calendar.events`.
2. `GET /auth/google/callback?code=...` → exchanges the code for tokens, verifies the ID token, upserts the user row (storing the encrypted refresh token), mints our JWT, sets it as an httpOnly cookie, redirects to the frontend dashboard.
3. `GET /auth/me` → returns the current user's profile (requires a valid JWT cookie).
4. `POST /auth/logout` → clears the cookie.
5. A `get_current_user` FastAPI dependency gates all protected endpoints (tasks, calendar, and later, voice-token issuance).

## 5. Error Handling

- **Consent denied** (user cancels on Google's screen) → callback redirects to the frontend with an error query param; frontend shows a friendly "login was cancelled" message rather than a raw error.
- **Expired/invalid JWT** → 401 with a structured error body (`{title, detail, type, status}`); frontend catches this and redirects to the login page.
- **Google token refresh failure** (e.g. user revoked access from their Google account) → the backend surfaces a specific error type so a later caller (including the voice agent) can tell the user "I couldn't access your calendar — please reconnect Google" instead of failing silently or with a generic 500.

## 6. CORS & Security

- CORS is configured from day one: `allow_origins` restricted to the frontend's dev/prod URL(s), `allow_credentials=True` (required for the cookie-based session to work cross-origin), restrictive `allow_methods`/`allow_headers`.
- `google_refresh_token` is encrypted at rest (Fernet symmetric encryption, key from settings/env) and is never included in any API response body.
- Rate limiting (Redis-backed) on `/auth/google/callback` and any endpoint that triggers an external API call or agent action.

## 7. Testing

- Unit tests for repositories against a test Postgres database (or transactional rollback per test).
- Unit tests for JWT mint/verify and Google ID token verification (mocking Google's JWKS endpoint).
- Integration test for the OAuth callback flow with a mocked Google token endpoint.
- Manual end-to-end verification of the real Google OAuth login in a browser — the consent screen itself can't be meaningfully automated.

## 8. Out of Scope (this sub-project)

- LiveKit voice pipeline (STT/agent/TTS) — sub-project 2.
- Agent function-calling actions (calendar booking, task management via voice) — sub-project 3.
- AWS deployment — sub-project 4.
- Redis-backed caching of Calendar API reads — deferred to sub-project 3, when calendar reads are actually implemented.
