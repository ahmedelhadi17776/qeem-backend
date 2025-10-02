"""Application configuration using Pydantic settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseModel):
    jwt_secret: str = Field(default="dev-secret", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expires_in_days: int = Field(default=7, alias="JWT_EXPIRES_IN_DAYS")


class SentrySettings(BaseModel):
    dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")

    # Core URLs
    database_url: str = Field(
        default="postgresql://elhadi:test123@localhost:5432/qeem", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # CORS
    cors_origins: List[str] = Field(default_factory=lambda: [
                                    "http://localhost:3000", "http://127.0.0.1:3000"], alias="CORS_ORIGINS")

    # Feature flags
    enable_ml_predictions: bool = Field(
        default=False, alias="ENABLE_ML_PREDICTIONS")
    enable_ai_negotiation: bool = Field(
        default=False, alias="ENABLE_AI_NEGOTIATION")
    enable_rate_limiting: bool = Field(
        default=False, alias="RATE_LIMITING_ENABLED")

    # Nested
    security: SecuritySettings = SecuritySettings()
    sentry: SentrySettings = SentrySettings()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached settings instance."""
    return AppSettings()
