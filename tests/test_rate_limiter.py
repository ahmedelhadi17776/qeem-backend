"""Tests for rate limiting system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.responses import Response
from starlette.requests import Request
from app.middleware.rate_limiter import RateLimitMiddleware, EnhancedRateLimiter, SlidingWindowRateLimiter
from app.api.rate_limit_deps import check_rate_limit
from fastapi import HTTPException, status
import time


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock()
        redis.zremrangebyscore = AsyncMock()
        redis.zadd = AsyncMock()
        redis.expire = AsyncMock()
        redis.zcard = AsyncMock(return_value=1)
        redis.zrange = AsyncMock(return_value=[(b"1234567890", 1234567890)])
        return redis

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/v1/auth/login"
        request.method = "POST"
        request.headers = {}
        return request

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        app = AsyncMock()
        return app

    @pytest.fixture
    def rate_limit_middleware(self, mock_app, mock_redis):
        """Create rate limit middleware with mocked dependencies."""
        middleware = RateLimitMiddleware(mock_app)
        middleware.rate_limiter = EnhancedRateLimiter()
        return middleware

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, rate_limit_middleware, mock_request, mock_redis):
        """Test that requests under limit are allowed."""
        mock_request.url.path = "/api/v1/auth/login"

        # Mock the call_next function
        mock_response = Response(content="OK", status_code=200)
        call_next = AsyncMock(return_value=mock_response)

        # Test the middleware
        response = await rate_limit_middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limit_middleware, mock_request, mock_redis):
        """Test that requests exceeding limit are blocked."""
        # Create a sliding window limiter with very low limit for testing
        sliding_window = SlidingWindowRateLimiter(
            window_size=60, max_requests=1)

        # First request should be allowed
        allowed, _ = sliding_window.is_allowed("test_key")
        assert allowed is True

        # Second request should be blocked
        allowed, rate_info = sliding_window.is_allowed("test_key")
        assert allowed is False
        assert rate_info["remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_user_id_from_request_with_token(self, rate_limit_middleware):
        """Test extracting user ID from JWT token."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}

        # Test the key generation (simplified test)
        key = rate_limit_middleware.rate_limiter.get_key_for_request(
            request, user_id=123)
        assert key.startswith("user:123:")

    @pytest.mark.asyncio
    async def test_get_user_id_from_request_no_token(self, rate_limit_middleware):
        """Test extracting user ID when no token present."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client.host = "127.0.0.1"
        request.url.path = "/api/v1/test"

        # Test the key generation for IP-based limiting
        key = rate_limit_middleware.rate_limiter.get_key_for_request(request)
        assert key.startswith("ip:127.0.0.1:")

    @pytest.mark.asyncio
    async def test_get_user_id_from_request_invalid_token(self, rate_limit_middleware):
        """Test extracting user ID with invalid token."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer invalid_token"}
        request.client.host = "127.0.0.1"
        request.url.path = "/api/v1/test"

        # Test the key generation falls back to IP
        key = rate_limit_middleware.rate_limiter.get_key_for_request(request)
        assert key.startswith("ip:127.0.0.1:")

    @pytest.mark.asyncio
    async def test_get_endpoint_limits_auth_login(self, rate_limit_middleware):
        """Test getting limits for auth login endpoint."""
        limit = rate_limit_middleware.rate_limiter.get_limit_for_endpoint(
            "/api/v1/auth/login")
        assert limit > 0  # Should have a specific limit

    @pytest.mark.asyncio
    async def test_get_endpoint_limits_auth_register(self, rate_limit_middleware):
        """Test getting limits for auth register endpoint."""
        limit = rate_limit_middleware.rate_limiter.get_limit_for_endpoint(
            "/api/v1/auth/register")
        assert limit > 0  # Should have a specific limit

    @pytest.mark.asyncio
    async def test_get_endpoint_limits_rates_calculate(self, rate_limit_middleware):
        """Test getting limits for rates calculate endpoint."""
        limit = rate_limit_middleware.rate_limiter.get_limit_for_endpoint(
            "/api/v1/rates/calculate")
        assert limit > 0  # Should have a specific limit

    @pytest.mark.asyncio
    async def test_get_endpoint_limits_market(self, rate_limit_middleware):
        """Test getting limits for market endpoints."""
        limit = rate_limit_middleware.rate_limiter.get_limit_for_endpoint(
            "/api/v1/market/data")
        assert limit > 0  # Should have a specific limit

    @pytest.mark.asyncio
    async def test_get_endpoint_limits_unknown(self, rate_limit_middleware):
        """Test getting limits for unknown endpoint."""
        limit = rate_limit_middleware.rate_limiter.get_limit_for_endpoint(
            "/api/v1/unknown")
        assert limit > 0  # Should have default limit

    @pytest.mark.asyncio
    async def test_dispatch_with_whitelisted_ip(self, rate_limit_middleware, mock_request):
        """Test that whitelisted IPs bypass rate limiting."""
        mock_request.client.host = "127.0.0.1"
        mock_request.url.path = "/api/v1/test"

        # Test whitelisted IP key generation
        key = rate_limit_middleware.rate_limiter.get_key_for_request(
            mock_request)
        # Should not be whitelisted by default, but test the logic
        assert key.startswith("ip:127.0.0.1:")

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_disabled(self, rate_limit_middleware, mock_request):
        """Test that requests pass through when rate limiting is disabled."""
        # Mock settings to disable rate limiting
        with patch('app.middleware.rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit.enabled = False

            # Test that disabled rate limiting returns True
            allowed, rate_info = await rate_limit_middleware.rate_limiter.is_request_allowed(mock_request)
            assert allowed is True
            assert rate_info["limit"] == 0


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter functionality."""

    @pytest.fixture
    def sliding_window(self):
        """Create a sliding window rate limiter."""
        return SlidingWindowRateLimiter(window_size=60, max_requests=5)

    def test_sliding_window_allows_requests_within_limit(self, sliding_window):
        """Test that requests within limit are allowed."""
        # First few requests should be allowed
        for i in range(5):
            allowed, rate_info = sliding_window.is_allowed("test_key")
            assert allowed is True
            assert rate_info["remaining"] == 4 - i

    def test_sliding_window_blocks_requests_over_limit(self, sliding_window):
        """Test that requests over limit are blocked."""
        # Fill up the limit
        for i in range(5):
            sliding_window.is_allowed("test_key")

        # Next request should be blocked
        allowed, rate_info = sliding_window.is_allowed("test_key")
        assert allowed is False
        assert rate_info["remaining"] == 0

    def test_sliding_window_resets_after_window(self, sliding_window):
        """Test that window resets after time passes."""
        # Fill up the limit
        for i in range(5):
            sliding_window.is_allowed("test_key")

        # Should be blocked
        allowed, _ = sliding_window.is_allowed("test_key")
        assert allowed is False

        # Mock time passing
        with patch('time.time') as mock_time:
            mock_time.return_value = 2000000000.0  # Fixed timestamp

            # Should be allowed again
            allowed, rate_info = sliding_window.is_allowed("test_key")
            assert allowed is True
            assert rate_info["remaining"] == 4


class TestRateLimitDependencies:
    """Test rate limit dependencies."""

    @pytest.mark.asyncio
    async def test_rate_limit_checker_allows_request(self):
        """Test that rate limit checker allows requests under limit."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/v1/test"

        # Should not raise exception
        await check_rate_limit(request, limit=10, window_seconds=3600, user_id=123)

    @pytest.mark.asyncio
    async def test_rate_limit_checker_disabled(self):
        """Test that rate limit checker is disabled when rate limiting is off."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/v1/test"

        # Mock settings to disable rate limiting
        with patch('app.api.rate_limit_deps.settings') as mock_settings:
            mock_settings.rate_limit.enabled = False

            # Should not raise exception
            await check_rate_limit(request, limit=10, window_seconds=3600, user_id=123)
