from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"

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

    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()  # type: ignore[call-arg]
