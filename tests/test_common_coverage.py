"""Tests for common modules to increase coverage."""

import pytest
from app.schemas.common import HealthResponse


class TestCommonCoverage:
    """Test common modules for coverage."""

    def test_health_response_schema(self):
        """Test HealthResponse schema."""
        health_data = {
            "status": "ok",
            "service": "qeem-backend"
        }
        health = HealthResponse(**health_data)
        assert health.status == "ok"
        assert health.service == "qeem-backend"

    def test_health_response_defaults(self):
        """Test HealthResponse with defaults."""
        health = HealthResponse()
        assert health.status == "ok"
        assert health.service == "qeem-backend"
