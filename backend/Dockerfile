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
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Now copy the actual source (plus the lockfile, this time for real —
# the bind mounts above were only visible during that one RUN step) and
# install the project itself. tests/ is excluded from the build context
# entirely via .dockerignore.
COPY pyproject.toml uv.lock ./
COPY app/ ./app
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-cache \
    uv sync --frozen --no-dev

# Runtime stage — no uv, no build tooling, no dependency cache, non-root user.
FROM python:3.13-slim

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app/ ./app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
