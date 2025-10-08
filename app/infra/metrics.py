"""Prometheus metrics collection for Qeem backend."""

import logging
import time
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

active_requests = Gauge("active_requests", "Number of active requests")

# Database metrics
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

db_connections_active = Gauge(
    "db_connections_active", "Number of active database connections"
)

db_connections_idle = Gauge(
    "db_connections_idle", "Number of idle database connections"
)

# Cache metrics
cache_hits_total = Counter(
    "cache_hits_total", "Total cache hits", ["cache_type", "key_pattern"]
)

cache_misses_total = Counter(
    "cache_misses_total", "Total cache misses", ["cache_type", "key_pattern"]
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "cache_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Business metrics
user_registrations_total = Counter(
    "user_registrations_total", "Total user registrations", ["method"]
)

user_logins_total = Counter("user_logins_total", "Total user logins", ["method"])

rate_calculations_total = Counter(
    "rate_calculations_total", "Total rate calculations", ["project_type", "complexity"]
)

email_sends_total = Counter(
    "email_sends_total", "Total emails sent", ["email_type", "status"]
)

# System metrics
application_info = Info("application_info", "Application information")

# Set application info
application_info.info(
    {"name": "qeem-backend", "version": "0.1.0", "environment": "development"}
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    async def dispatch(self, request: Request, call_next):
        """Collect metrics for each request."""
        start_time = time.time()
        active_requests.inc()

        try:
            response = await call_next(request)

            # Extract endpoint name (remove path parameters)
            endpoint = self._extract_endpoint(request.url.path)

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            return response

        except Exception:
            # Record error metrics
            endpoint = self._extract_endpoint(request.url.path)
            http_requests_total.labels(
                method=request.method, endpoint=endpoint, status_code=500
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            raise

        finally:
            active_requests.dec()

    def _extract_endpoint(self, path: str) -> str:
        """Extract endpoint name from path."""
        # Replace path parameters with placeholders
        import re

        # Common patterns
        patterns = [
            (r"/\d+", "/{id}"),
            (r"/[a-f0-9-]{36}", "/{uuid}"),
            (r"/[a-f0-9-]{32}", "/{token}"),
        ]

        endpoint = path
        for pattern, replacement in patterns:
            endpoint = re.sub(pattern, replacement, endpoint)

        return endpoint


def record_db_query(operation: str, table: str):
    """Decorator to record database query metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration_seconds.labels(
                    operation=operation, table=table
                ).observe(duration)

        return wrapper

    return decorator


def record_cache_operation(operation: str, cache_type: str):
    """Decorator to record cache operation metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                cache_operations_duration_seconds.labels(
                    operation=operation, cache_type=cache_type
                ).observe(duration)

        return wrapper

    return decorator


def record_cache_hit(cache_type: str, key_pattern: str):
    """Record cache hit."""
    cache_hits_total.labels(cache_type=cache_type, key_pattern=key_pattern).inc()


def record_cache_miss(cache_type: str, key_pattern: str):
    """Record cache miss."""
    cache_misses_total.labels(cache_type=cache_type, key_pattern=key_pattern).inc()


def record_user_registration(method: str = "email"):
    """Record user registration."""
    user_registrations_total.labels(method=method).inc()


def record_user_login(method: str = "email"):
    """Record user login."""
    user_logins_total.labels(method=method).inc()


def record_rate_calculation(project_type: str, complexity: str):
    """Record rate calculation."""
    rate_calculations_total.labels(
        project_type=project_type, complexity=complexity
    ).inc()


def record_email_send(email_type: str, status: str = "success"):
    """Record email send."""
    email_sends_total.labels(email_type=email_type, status=status).inc()


def update_db_connection_metrics(active: int, idle: int):
    """Update database connection metrics."""
    db_connections_active.set(active)
    db_connections_idle.set(idle)


def get_metrics_response() -> Response:
    """Get Prometheus metrics response."""
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
