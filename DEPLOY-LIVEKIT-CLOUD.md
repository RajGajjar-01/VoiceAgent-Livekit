# Plan: move the agent worker to LiveKit Cloud

There is no room to deploy. Rooms get created on demand (`assistant-{user_id}-{uuid}`) when the frontend joins with a backend-minted token. The thing we deploy is the **agent worker** (`app.agent.worker`), which moves from Railway to LiveKit Cloud Agents. The backend, frontend, Postgres and Redis stay on Railway.

```
Frontend (Railway) ──token──> Backend (Railway) ──> Postgres/Redis (Railway)
     │                                                   ▲
     └──WebRTC──> LiveKit Cloud room ──dispatch──> Agent (LiveKit Cloud)
```

## 0. Prereqs
- Install the CLI: `curl -sSL https://get.livekit.io/cli | bash`, then `lk cloud auth` and pick the same project the backend's `LIVEKIT_*` keys belong to.
- Railway Postgres has to be reachable from outside Railway. Turn on its **public TCP proxy** and use that `DATABASE_URL`. `*.railway.internal` will not resolve from LiveKit Cloud.

## 1. Dockerfile split (`backend/`)
`lk agent create` builds `./Dockerfile` from the working directory. The current one runs the API.
- `git mv Dockerfile Dockerfile.api`, then set `RAILWAY_DOCKERFILE_PATH=Dockerfile.api` on the Railway backend service.
- New `Dockerfile` for the agent: same builder stage, non-root `python:3.13-slim` runtime (glibc, not Alpine), plus:
  ```dockerfile
  RUN python -m app.agent.worker download-files   # prefetch Silero VAD at build time
  CMD ["python", "-m", "app.agent.worker", "start"]
  ```
  Drop `EXPOSE`, `HEALTHCHECK`, alembic and `sh -c`. The backend still runs migrations.
- Make sure `ca-certificates` is in the image. The LiveKit SDK needs it for TLS.

## 2. Secrets file (`backend/.env.agent`, gitignored, never committed)
LiveKit Cloud injects `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`. Do **not** set those. `config.py` already reads them from the environment, so no code change is needed. Everything the worker touches goes in this file:
```
DATABASE_URL=<railway public proxy url>
GOOGLE_CLIENT_ID=  GOOGLE_CLIENT_SECRET=  GOOGLE_REDIRECT_URI=
REFRESH_TOKEN_ENCRYPTION_KEY=   # must match backend, decrypts stored Google tokens
JWT_SECRET=                     # required by Settings even if unused here
DEEPGRAM_API_KEY=  ELEVENLABS_API_KEY=  ELEVENLABS_VOICE_ID=
LLM_API_KEY=  LLM_BASE_URL=  LLM_MODEL=
CLOUDFLARE_ACCOUNT_ID=  CLOUDFLARE_API_KEY=  FALLBACK_LLM_MODEL=
ENVIRONMENT=production  LOG_LEVEL=INFO
# required by Settings, unused by the worker (placeholders are fine):
REDIS_URL=redis://unused:6379/0  FRONTEND_URL=https://unused  ALLOWED_ORIGINS=[]
```
A missing required field crashes the worker on boot.

## 3. Deploy
```bash
cd backend
lk agent create --region <closest to Railway DB region> --secrets-file .env.agent
# writes livekit.toml (commit it). Later deploys:
lk agent deploy
lk agent status && lk agent logs
```

## 4. Cutover (order matters)
1. **Stop the Railway worker service first.** Two workers on one project split dispatch and calls fail at random (see README).
2. Stop any local `worker dev` too.
3. Smoke test from the prod frontend: start a call, create a task, book an event, end the call, and check that the conversation is saved.
4. Once that passes, delete the Railway worker service and update the README's Deploying section and diagram.

## Rollback
`lk agent rollback`, or scale the Railway worker back up after `lk agent delete`. Never run both at once.

## Risks
- DB latency: every tool call goes from LiveKit Cloud to Railway. Pick a region close to it.
- Exposing the Railway Postgres proxy publicly means it relies on a strong password alone. Rotate it if it is the default.
- No `agent_name` is set, so auto-dispatch keeps working. Setting one later would require explicit dispatch from the backend.
