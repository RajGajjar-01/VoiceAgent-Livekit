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
