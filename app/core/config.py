from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # Google Gemini Configuration
    gemini_api_key: str = "development_mock_key"
    gemini_model: str = "gemini-2.5-flash"

    # Application Environment
    app_env: str = "development"
    log_level: str = "INFO"

    # AI Service Settings
    ai_timeout_seconds: float = 30.0
    ai_max_retries: int = 2

    # Rate Limiting
    rate_limit_requests_per_minute: int = 15

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()

