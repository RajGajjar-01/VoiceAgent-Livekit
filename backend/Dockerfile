# Builder stage — installs dependencies and the project into a venv.
# Kept separate from the runtime stage so build tooling and the uv cache
# never end up in the final image.
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first, in their own layer, using only the lockfile.
# This layer is cache-hit as long as pyproject.toml/uv.lock don't change,
# so editing app code doesn't force a full dependency reinstall.
# --no-dev: dev tooling (pytest, ruff, mypy) is never installed into the
# image — tests are not run inside Docker, only in CI/local dev.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Now copy the actual source and install the project itself. tests/ is
# excluded from the build context entirely via .dockerignore.
COPY app/ ./app
RUN uv sync --frozen --no-dev

# Runtime stage — no uv, no build tooling, no dependency cache, non-root user.
FROM python:3.13-slim

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app/ ./app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic/ ./alembic

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')" || exit 1

# Run pending migrations before serving — the "users"/etc. tables won't
# exist on a fresh database otherwise. alembic tracks the applied revision,
# so this is a no-op once the DB is up to date.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
