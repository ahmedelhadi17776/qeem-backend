"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, engine as app_engine
from app.models.base import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Create tables for isolated test DB
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint(self):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "service": "qeem-backend"
        }


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_endpoint_exists(self):
        """Test login endpoint exists."""
        response = client.post("/api/v1/auth/login")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


class TestRatesEndpoints:
    """Test rate calculation endpoints."""

    def test_rates_history_endpoint_exists(self):
        """Test rates history endpoint exists."""
        response = client.get("/api/v1/rates/history")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_docs_endpoint(self):
        """Test API docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
