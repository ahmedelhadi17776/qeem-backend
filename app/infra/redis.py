"""Redis client factory with graceful degradation."""

import logging
from functools import lru_cache
from typing import Optional

import redis

from ..core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis() -> Optional[redis.Redis]:
    """Get Redis client with graceful degradation.

    Returns:
        Redis client if available, None if connection fails
    """
    try:
        settings = get_settings()
        client = redis.from_url(settings.redis_url, decode_responses=True)
        # Test connection
        client.ping()
        logger.info("Redis connection established")
        return client
    except Exception as exc:
        logger.warning(f"Redis connection failed: {exc}")
        return None


def is_redis_available() -> bool:
    """Check if Redis is available.

    Returns:
        True if Redis is available, False otherwise
    """
    return get_redis() is not None
