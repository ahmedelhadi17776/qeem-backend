"""Infrastructure module."""

from .redis import get_redis, is_redis_available
from .metrics import (
    MetricsMiddleware,
    record_db_query,
    record_cache_operation,
    record_cache_hit,
    record_cache_miss,
    record_user_registration,
    record_user_login,
    record_rate_calculation,
    record_email_send,
    update_db_connection_metrics,
    get_metrics_response,
)

__all__ = [
    "get_redis",
    "is_redis_available",
    "MetricsMiddleware",
    "record_db_query",
    "record_cache_operation",
    "record_cache_hit",
    "record_cache_miss",
    "record_user_registration",
    "record_user_login",
    "record_rate_calculation",
    "record_email_send",
    "update_db_connection_metrics",
    "get_metrics_response",
]
