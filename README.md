# Voice Agent — LiveKit

A voice-driven AI agent with Google authentication: users sign in with Google, then talk to a real-time voice assistant (LiveKit) that can answer questions and take actions like booking calendar events or managing tasks.

## Architecture

- **Backend:** FastAPI (Python 3.13, async), SQLAlchemy 2.x + Alembic on PostgreSQL, Redis (rate limiting), Google OAuth 2.0 for auth (JWT session cookie — no password auth).
- **Frontend:** React + Vite + TypeScript, Tailwind v4, shadcn/ui.
- **Voice pipeline:** LiveKit Cloud + LiveKit Agents (Python) — not yet implemented.

This project is being built incrementally; the sections below reflect what's actually in place right now, not the full end-state.

## Current status

**Backend** (`backend/`): project scaffolded with `uv`, dependencies installed (FastAPI, SQLAlchemy[asyncio], asyncpg, Alembic, pydantic-settings, PyJWT, cryptography, google-auth, httpx, fastapi-limiter, redis) and dev tooling (pytest, pytest-asyncio, ruff, mypy). Package folders (`app/api`, `app/core`, `app/models`, `app/repositories`, `app/schemas`) are scaffolded but not yet implemented — no app code, database models, migrations, or dev infra (Docker Compose for Postgres/Redis) exist yet.

**Frontend** (`frontend/`): scaffolded with Vite + React + TypeScript. Tailwind v4 and shadcn/ui are configured, with a full set of shadcn components installed (button, card, sidebar, sonner, dropdown-menu, avatar, skeleton, separator, badge, input, label, tabs, tooltip, textarea, alert, field, sheet). App-level dependencies installed: axios, zustand, react-router, react-hook-form, zod, next-themes. No app code (routing, auth store, pages) has been written yet.

## Setup (current)

### Backend

```bash
cd backend
uv sync
```

### Frontend

Uses `pnpm` (not npm/yarn) — enforced via the `packageManager` field in `package.json`.

```bash
cd frontend
pnpm install
pnpm dev
```
