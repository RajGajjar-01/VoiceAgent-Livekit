import os

# Set before any test module (and therefore app.core.config) is imported.
# app.core.config creates `settings` as a module-level singleton at import
# time, so an autouse fixture using monkeypatch.setenv() would run too late
# to affect it — pytest fixtures execute after collection/import, not before.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-at-least-32-bytes-long-for-hs256")
os.environ.setdefault("REFRESH_TOKEN_ENCRYPTION_KEY", "kX9m2vQZ8pL4nR7tY1wB3cF6hJ0sA5dGjKvM8xN2oQw=")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:5173"]')
