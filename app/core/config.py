"""Application configuration using Pydantic settings."""

import json
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from secrets import token_urlsafe


class DatabaseSettings(BaseModel):
    pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=30, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")
    echo: bool = Field(default=False, alias="DB_ECHO")


class RateLimitSettings(BaseModel):
    enabled: bool = Field(default=False, alias="RATE_LIMITING_ENABLED")
    default_limit: int = Field(default=100, alias="RATE_LIMIT_DEFAULT")
    window_seconds: int = Field(default=3600, alias="RATE_LIMIT_WINDOW_SECONDS")
    burst_limit: int = Field(default=200, alias="RATE_LIMIT_BURST")

    # Endpoint-specific limits
    auth_login_limit: int = Field(default=5, alias="RATE_LIMIT_AUTH_LOGIN")
    auth_register_limit: int = Field(default=3, alias="RATE_LIMIT_AUTH_REGISTER")
    rates_calculate_limit: int = Field(default=20, alias="RATE_LIMIT_RATES_CALCULATE")
    market_limit: int = Field(default=30, alias="RATE_LIMIT_MARKET")

    # User-based limits (for authenticated users)
    user_limit_multiplier: float = Field(
        default=2.0, alias="RATE_LIMIT_USER_MULTIPLIER"
    )

    # Whitelist configuration
    whitelist_ips: List[str] = Field(
        default_factory=list, alias="RATE_LIMIT_WHITELIST_IPS"
    )


class EmailSettings(BaseModel):
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@qeem.com", alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    verification_token_ttl_hours: int = Field(
        default=24, alias="VERIFICATION_TOKEN_TTL_HOURS"
    )
    enable_email_verification: bool = Field(
        default=True, alias="ENABLE_EMAIL_VERIFICATION"
    )


class SecuritySettings(BaseModel):
    jwt_secret: Optional[str] = Field(default=None, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expires_in_days: int = Field(default=7, alias="JWT_EXPIRES_IN_DAYS")


class SentrySettings(BaseModel):
    dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Core URLs
    database_url: str = Field(
        default="postgresql://elhadi:test123@localhost:5432/qeem", alias="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # CORS
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS"
    )
    cors_origins: List[str] = Field(default_factory=list)

    # Feature flags
    enable_ml_predictions: bool = Field(default=False, alias="ENABLE_ML_PREDICTIONS")
    enable_ai_negotiation: bool = Field(default=False, alias="ENABLE_AI_NEGOTIATION")
    enable_rate_limiting: bool = Field(default=False, alias="RATE_LIMITING_ENABLED")
    market_cache_ttl: int = Field(default=3600, alias="MARKET_CACHE_TTL")

    # Nested
    security: SecuritySettings = SecuritySettings()
    sentry: SentrySettings = SentrySettings()
    database: DatabaseSettings = DatabaseSettings()
    email: EmailSettings = EmailSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()

    @model_validator(mode="after")
    def _validate_urls(self) -> "AppSettings":
        """Validate database and Redis URL formats."""
        if not self.database_url.startswith(("postgresql://", "sqlite://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or 'sqlite://'"
            )
        if not self.redis_url.startswith("redis://"):
            raise ValueError("REDIS_URL must start with 'redis://'")
        return self

    @model_validator(mode="after")
    def _ensure_jwt_secret(self) -> "AppSettings":
        """Ensure JWT secret policy by environment.

        - development: auto-generate a random secret if not provided
        - ci/test: be more lenient, auto-generate if needed
        - non-development: require a strong secret (min length 32)
        """
        secret = self.security.jwt_secret
        if self.environment in ["development", "ci", "test"]:
            if not secret or len(secret) < 16:
                # Generate an ephemeral secret for local dev/CI if missing/weak
                self.security.jwt_secret = token_urlsafe(32)
            return self

        # Non-development environments must provide a strong secret
        if not secret or len(secret) < 32:
            raise ValueError(
                "JWT_SECRET must be set to a secure value (length >= 32) "
                "in non-development environments"
            )
        return self

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
                origin.strip()
                for origin in self.cors_origins_str.split(",")
                if origin.strip()
            ]
        return self


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached settings instance."""
    return AppSettings()
