from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Set DATABASE_URL directly (e.g. Railway's managed Postgres plugin), or
    # leave it unset and provide the discrete POSTGRES_* vars instead (used
    # for local dev via docker-compose).
    DATABASE_URL: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str | None = None

    REDIS_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    JWT_SECRET: str
    JWT_EXPIRY_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRY_DAYS: int = 7
    REFRESH_TOKEN_ENCRYPTION_KEY: str

    FRONTEND_URL: str
    ALLOWED_ORIGINS: list[str]
    COOKIE_SECURE: bool = False

    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    DEEPGRAM_API_KEY: str

    # Generic LLM_* names (not GROQ_*) so swapping providers is an .env
    # change, not a code change — LLM_BASE_URL just needs to point at any
    # OpenAI-compatible chat completions endpoint.
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Fallback LLM, used via FallbackAdapter when the primary provider errors
    # (e.g. Groq's free-tier rate limits). Optional — if either is unset, the
    # worker runs with just the primary LLM and no fallback.
    CLOUDFLARE_ACCOUNT_ID: str | None = None
    CLOUDFLARE_API_KEY: str | None = None
    FALLBACK_LLM_MODEL: str = "@cf/moonshotai/kimi-k2.7-code"

    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            # Railway (and most managed providers) hand out postgres:// or
            # postgresql:// URLs; SQLAlchemy's async engine needs the
            # +asyncpg driver in the scheme.
            return self.DATABASE_URL.replace("postgres://", "postgresql://", 1).replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        if not (self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_SERVER and self.POSTGRES_DB):
            raise ValueError(
                "Set DATABASE_URL, or all of POSTGRES_USER/POSTGRES_PASSWORD/"
                "POSTGRES_SERVER/POSTGRES_DB"
            )
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
