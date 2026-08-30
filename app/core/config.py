from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "URL Shortener"
    BASE_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://url_shortener:url_shortener@localhost:5434/url_shortener_test"
    )
    REDIS_URL: str = "redis://localhost:6381"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TELEGRAM_BOT_TOKEN: str | None = None
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
