from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # Google Gemini Configuration
    gemini_api_key: str = "development_mock_key"
    gemini_model: str = "gemini-3.8-flash"

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
    # Use union str | list[str] so pydantic-settings doesn't attempt json.loads("") on empty env string
    cors_origins: str | list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="before")
    @classmethod
    def ignore_empty_env_strings(cls, values: Any) -> Any:
        """Strip empty or whitespace-only environment strings so default values apply.

        Prevents deployment errors on platforms like Vercel where unset environment
        variables are provided as empty strings (""), causing integer/float parsing errors.
        """
        if isinstance(values, dict):
            cleaned: dict[str, Any] = {}
            for k, v in values.items():
                if isinstance(v, str) and v.strip() == "":
                    continue
                cleaned[k] = v
            return cleaned
        return values

    @field_validator("cors_origins", mode="after")
    @classmethod
    def ensure_cors_list(cls, v: Any) -> list[str]:
        """Ensure cors_origins is always returned as a list of strings."""
        if isinstance(v, str):
            cleaned = [item.strip() for item in v.split(",") if item.strip()]
            return cleaned or ["*"]
        return list(v)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
