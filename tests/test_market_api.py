from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_statistics_endpoint_ok():
    r = client.get("/api/v1/market/statistics?limit=2")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_trends_endpoint_ok():
    r = client.get("/api/v1/market/trends?window=3")
    assert r.status_code == 200
    body = r.json()
    assert "points" in body
