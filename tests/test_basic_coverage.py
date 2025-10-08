"""Basic tests to increase coverage."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestBasicCoverage:
    """Basic tests for coverage increase."""

    def test_health_endpoint(self):
        """Test health endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        # Health endpoint may return 'unhealthy' if database is not available in test
        data = response.json()
        assert "service" in data
        assert data["service"] == "qeem-backend"

    def test_openapi_endpoint(self):
        """Test OpenAPI endpoint."""
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_docs_endpoint(self):
        """Test docs endpoint."""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """Test redoc endpoint."""
        client = TestClient(app)
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_auth_login_endpoint_exists(self):
        """Test auth login endpoint exists."""
        client = TestClient(app)
        response = client.post("/api/v1/auth/login")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_auth_register_endpoint_exists(self):
        """Test auth register endpoint exists."""
        client = TestClient(app)
        response = client.post("/api/v1/auth/register")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_rates_endpoint_exists(self):
        """Test rates endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/rates/calculate")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_rates_history_endpoint_exists(self):
        """Test rates history endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/v1/rates/history")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
