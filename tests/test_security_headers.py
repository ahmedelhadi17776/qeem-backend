"""Tests for security headers middleware."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request
from starlette.responses import Response
from app.middleware.security import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """Test security headers middleware functionality."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock ASGI app."""
        app = MagicMock()
        app.dispatch = AsyncMock()
        return app

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        response = MagicMock(spec=Response)
        response.headers = {}
        return response

    @pytest.fixture
    def security_middleware_production(self, mock_app):
        """Create security middleware for production environment."""
        return SecurityHeadersMiddleware(mock_app, environment="production")

    @pytest.fixture
    def security_middleware_development(self, mock_app):
        """Create security middleware for development environment."""
        return SecurityHeadersMiddleware(mock_app, environment="development")

    @pytest.mark.asyncio
    async def test_security_headers_production(self, security_middleware_production, mock_request, mock_response):
        """Test security headers in production environment."""
        security_middleware_production.app.dispatch.return_value = mock_response

        result = await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        assert result == mock_response
        assert "X-Content-Type-Options" in mock_response.headers
        assert mock_response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in mock_response.headers
        assert mock_response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in mock_response.headers
        assert mock_response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in mock_response.headers
        assert "Content-Security-Policy" in mock_response.headers
        assert "Referrer-Policy" in mock_response.headers

    @pytest.mark.asyncio
    async def test_security_headers_development(self, security_middleware_development, mock_request, mock_response):
        """Test security headers in development environment."""
        security_middleware_development.app.dispatch.return_value = mock_response

        result = await security_middleware_development.dispatch(mock_request, security_middleware_development.app.dispatch)

        assert result == mock_response
        assert "X-Content-Type-Options" in mock_response.headers
        assert mock_response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in mock_response.headers
        assert mock_response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in mock_response.headers
        assert mock_response.headers["X-XSS-Protection"] == "1; mode=block"
        # HSTS should not be set in development
        assert "Strict-Transport-Security" not in mock_response.headers
        # CSP should be more permissive in development
        assert "Content-Security-Policy" in mock_response.headers
        csp = mock_response.headers["Content-Security-Policy"]
        assert "unsafe-inline" in csp

    @pytest.mark.asyncio
    async def test_hsts_header_production(self, security_middleware_production, mock_request, mock_response):
        """Test HSTS header in production."""
        security_middleware_production.app.dispatch.return_value = mock_response

        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        hsts = mock_response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    @pytest.mark.asyncio
    async def test_csp_header_production(self, security_middleware_production, mock_request, mock_response):
        """Test CSP header in production."""
        security_middleware_production.app.dispatch.return_value = mock_response

        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        csp = mock_response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data:" in csp
        assert "font-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_csp_header_development(self, security_middleware_development, mock_request, mock_response):
        """Test CSP header in development."""
        security_middleware_development.app.dispatch.return_value = mock_response

        await security_middleware_development.dispatch(mock_request, security_middleware_development.app.dispatch)

        csp = mock_response.headers["Content-Security-Policy"]
        assert "unsafe-inline" in csp
        assert "unsafe-eval" in csp

    @pytest.mark.asyncio
    async def test_referrer_policy_header(self, security_middleware_production, mock_request, mock_response):
        """Test Referrer-Policy header."""
        security_middleware_production.app.dispatch.return_value = mock_response

        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        assert mock_response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_all_required_headers_present(self, security_middleware_production, mock_request, mock_response):
        """Test that all required security headers are present."""
        security_middleware_production.app.dispatch.return_value = mock_response

        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy"
        ]

        for header in required_headers:
            assert header in mock_response.headers, f"Missing required header: {header}"

    @pytest.mark.asyncio
    async def test_headers_not_duplicated(self, security_middleware_production, mock_request, mock_response):
        """Test that headers are not duplicated."""
        security_middleware_production.app.dispatch.return_value = mock_response

        # Call dispatch multiple times
        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)
        await security_middleware_production.dispatch(mock_request, security_middleware_production.app.dispatch)

        # Headers should be set only once
        # All required headers present exactly once (6 basic headers + 1 Permissions-Policy)
        assert len(mock_response.headers) == 7
