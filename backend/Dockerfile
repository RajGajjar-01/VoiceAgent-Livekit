# Agent worker image for LiveKit Cloud (`lk agent create/deploy` builds ./Dockerfile).
# The API image lives in Dockerfile.api (Railway: RAILWAY_DOCKERFILE_PATH=Dockerfile.api).
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app/ ./app
RUN uv sync --frozen --no-dev

FROM python:3.13-slim

# LiveKit SDK needs CA certs for TLS.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app/ ./app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app

# LIVEKIT_URL/API_KEY/API_SECRET are injected by LiveKit Cloud; the rest come from agent secrets.
CMD ["python", "-m", "app.agent.worker", "start"]
