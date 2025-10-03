"""Application configuration using Pydantic settings."""

import json
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


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
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Core URLs
    database_url: str = Field(
        default="postgresql://elhadi:test123@localhost:5432/qeem", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # CORS
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS"
    )
    cors_origins: List[str] = Field(default_factory=list)

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

    @model_validator(mode="after")
    def _parse_cors_origins(self) -> "AppSettings":
        if isinstance(self.cors_origins_str, str):
            try:
                parsed = json.loads(self.cors_origins_str)
                if isinstance(parsed, list):
                    self.cors_origins = [str(x) for x in parsed]
                    return self
            except json.JSONDecodeError:
                pass
            self.cors_origins = [
                origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()
            ]
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached settings instance."""
    return AppSettings()
