"""Rate limiting dependencies for endpoint-specific limits."""

import logging
from typing import Optional

from fastapi import Request, HTTPException, status

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self, detail: str = "Rate limit exceeded", headers: Optional[dict] = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or {},
        )


async def check_rate_limit(
    request: Request,
    limit: int,
    window_seconds: int = 3600,
    user_id: Optional[int] = None,
) -> None:
    """Check rate limit for a specific endpoint.

    Args:
        request: FastAPI request object
        limit: Maximum requests allowed
        window_seconds: Time window in seconds
        user_id: User ID for user-based limiting

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    if not settings.rate_limit.enabled:
        return

    # This is a simplified implementation
    # In production, you'd integrate with the Redis rate limiter
    # For now, we'll just log the check
    logger.info(
        f"Rate limit check: {limit} requests per {window_seconds}s for user {user_id}"
    )


def rate_limit(limit: int, window_seconds: int = 3600):
    """Decorator for endpoint-specific rate limiting."""

    async def rate_limit_dependency(request: Request):
        # For auth endpoints, we don't require authentication
        # Just log the rate limit check
        logger.info(f"Rate limit check: {limit} requests per {window_seconds}s")
        return None

    return rate_limit_dependency


# Predefined rate limit dependencies
auth_login_rate_limit = rate_limit(
    limit=settings.rate_limit.auth_login_limit, window_seconds=60  # 1 minute
)

auth_register_rate_limit = rate_limit(
    limit=settings.rate_limit.auth_register_limit, window_seconds=300  # 5 minutes
)

rates_calculate_rate_limit = rate_limit(
    limit=settings.rate_limit.rates_calculate_limit, window_seconds=3600  # 1 hour
)

market_rate_limit = rate_limit(
    limit=settings.rate_limit.market_limit, window_seconds=3600  # 1 hour
)
