"""Enhanced rate limiting with sliding window and token bucket algorithms."""

import logging
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import get_settings
from ..infra.redis import get_redis, is_redis_available

logger = logging.getLogger(__name__)
settings = get_settings()


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation."""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # seconds
        self.max_requests = max_requests
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed for the given key."""
        now = time.time()
        window_start = now - self.window_size

        # Clean old requests
        if key in self.requests:
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()

        # Check if under limit
        current_count = len(self.requests[key])
        if current_count >= self.max_requests:
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset_time": int(self.requests[key][0] + self.window_size),
            }

        # Add current request
        self.requests[key].append(now)

        return True, {
            "limit": self.max_requests,
            "remaining": self.max_requests - current_count - 1,
            "reset_time": int(now + self.window_size),
        }


class TokenBucketRateLimiter:
    """Token bucket rate limiter for burst handling."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens: Dict[str, float] = defaultdict(lambda: capacity)
        self.last_refill: Dict[str, float] = defaultdict(time.time)

    def is_allowed(
        self, key: str, tokens_needed: int = 1
    ) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed for the given key."""
        now = time.time()

        # Refill tokens
        time_passed = now - self.last_refill[key]
        tokens_to_add = time_passed * self.refill_rate
        self.tokens[key] = min(self.capacity, self.tokens[key] + tokens_to_add)
        self.last_refill[key] = now

        # Check if enough tokens
        if self.tokens[key] >= tokens_needed:
            self.tokens[key] -= tokens_needed
            return True, {
                "limit": self.capacity,
                "remaining": int(self.tokens[key]),
                "reset_time": int(
                    now + (self.capacity - self.tokens[key]) / self.refill_rate
                ),
            }

        return False, {
            "limit": self.capacity,
            "remaining": int(self.tokens[key]),
            "reset_time": int(
                now + (tokens_needed - self.tokens[key]) / self.refill_rate
            ),
        }


class RedisRateLimiter:
    """Redis-based rate limiter for distributed systems."""

    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests

    async def is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed using Redis."""
        if not is_redis_available():
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset_time": 0,
            }

        try:
            redis = get_redis()
            if not redis:
                return True, {
                    "limit": self.max_requests,
                    "remaining": self.max_requests,
                    "reset_time": 0,
                }

            # Use sliding window with Redis
            now = time.time()
            window_start = now - self.window_size

            # Remove old entries
            redis.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_count_result = redis.zcard(key)
            current_count = (
                await current_count_result
                if hasattr(current_count_result, "__await__")
                else current_count_result
            )

            if current_count >= self.max_requests:
                # Get oldest request time for reset calculation
                oldest_requests_result = redis.zrange(key, 0, 0, withscores=True)
                oldest_requests = (
                    await oldest_requests_result
                    if hasattr(oldest_requests_result, "__await__")
                    else oldest_requests_result
                )
                reset_time = (
                    int(oldest_requests[0][1] + self.window_size)
                    if oldest_requests
                    else int(now + self.window_size)
                )

                return False, {
                    "limit": self.max_requests,
                    "remaining": 0,
                    "reset_time": reset_time,
                }

            # Add current request
            redis.zadd(key, {str(now): now})
            redis.expire(key, self.window_size)

            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests - int(current_count) - 1,
                "reset_time": int(now + self.window_size),
            }

        except Exception as e:
            logger.warning(f"Redis rate limiter error: {e}")
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset_time": 0,
            }


class EnhancedRateLimiter:
    """Enhanced rate limiter with multiple strategies."""

    def __init__(self):
        self.sliding_window = SlidingWindowRateLimiter(
            window_size=settings.rate_limit.window_seconds,
            max_requests=settings.rate_limit.default_limit,
        )
        self.token_bucket = TokenBucketRateLimiter(
            capacity=settings.rate_limit.burst_limit,
            refill_rate=settings.rate_limit.default_limit
            / settings.rate_limit.window_seconds,
        )
        self.redis_limiter = RedisRateLimiter(
            window_size=settings.rate_limit.window_seconds,
            max_requests=settings.rate_limit.default_limit,
        )

    def get_limit_for_endpoint(self, path: str) -> int:
        """Get rate limit for specific endpoint."""
        if "/auth/login" in path:
            return settings.rate_limit.auth_login_limit
        elif "/auth/register" in path:
            return settings.rate_limit.auth_register_limit
        elif "/rates/calculate" in path:
            return settings.rate_limit.rates_calculate_limit
        elif "/market/" in path:
            return settings.rate_limit.market_limit
        else:
            return settings.rate_limit.default_limit

    def get_key_for_request(
        self, request: Request, user_id: Optional[int] = None
    ) -> str:
        """Generate rate limit key for request."""
        client_ip = request.client.host if request.client else "unknown"

        # Check if IP is whitelisted
        if client_ip in settings.rate_limit.whitelist_ips:
            return f"whitelist:{client_ip}"

        # Use user-based key if authenticated
        if user_id:
            return f"user:{user_id}:{request.url.path}"

        # Use IP-based key for anonymous users
        return f"ip:{client_ip}:{request.url.path}"

    async def is_request_allowed(
        self, request: Request, user_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, int]]:
        """Check if request is allowed."""
        if not settings.rate_limit.enabled:
            return True, {"limit": 0, "remaining": 0, "reset_time": 0}

        key = self.get_key_for_request(request, user_id)
        limit = self.get_limit_for_endpoint(str(request.url.path))

        # Use Redis if available, otherwise fallback to in-memory
        if is_redis_available():
            # Create Redis limiter with endpoint-specific limit
            redis_limiter = RedisRateLimiter(
                window_size=settings.rate_limit.window_seconds, max_requests=limit
            )
            return await redis_limiter.is_allowed(key)
        else:
            # Fallback to sliding window
            sliding_window = SlidingWindowRateLimiter(
                window_size=settings.rate_limit.window_seconds, max_requests=limit
            )
            return sliding_window.is_allowed(key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = EnhancedRateLimiter()

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""

        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Get user ID if authenticated
        user_id = None
        try:
            # Try to get current user without raising exceptions
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Extract user ID from token (simplified)
                # In production, you'd properly decode the JWT
                pass
        except Exception as e:
            logger.debug(f"Error extracting user from auth header: {e}")

        # Check rate limit
        allowed, rate_info = await self.rate_limiter.is_request_allowed(
            request, user_id
        )

        if not allowed:
            response = Response(
                content="Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
            response.headers["Retry-After"] = str(
                rate_info["reset_time"] - int(time.time())
            )
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])

        return response


def get_rate_limit_middleware():
    """Get rate limiting middleware."""
    return RateLimitMiddleware
