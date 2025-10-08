"""Tests for market API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.fixture
def client(db_session):
    """Create test client with database session override."""
    from app.db.database import get_db

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_statistics_endpoint_ok(client):
    """Test market statistics endpoint."""
    r = client.get("/api/v1/market/statistics?limit=2")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_trends_endpoint_ok(client):
    """Test market trends endpoint."""
    r = client.get("/api/v1/market/trends?window=3")
    assert r.status_code == 200
    body = r.json()
    assert "points" in body
