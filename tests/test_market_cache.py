"""Cache behavior tests for market service using a fake Redis."""

import pytest
import json
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import market as market_service
from app.schemas.market import MarketStatisticsQuery, MarketTrendsQuery


class FakeRedis:
    def __init__(self):
        self.store: Dict[str, str] = {}
        self.ttl: Dict[str, int] = {}

    def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value
        self.ttl[key] = ttl


@pytest.mark.asyncio
async def test_market_statistics_cache_hit_and_store(monkeypatch, db_session: AsyncSession):
    fake = FakeRedis()

    # monkeypatch redis factory
    monkeypatch.setattr(market_service, "get_redis", lambda: fake)

    # first call should store
    q = MarketStatisticsQuery(limit=1, offset=0)
    resp1 = await market_service.get_market_statistics(db_session, q)
    assert resp1.cached is False

    # ensure setex happened
    assert any(k.startswith("market:stats:") for k in fake.store.keys())

    # second call should hit cache
    resp2 = await market_service.get_market_statistics(db_session, q)
    assert resp2.cached is True


@pytest.mark.asyncio
async def test_market_trends_cache_hit_and_store(monkeypatch, db_session: AsyncSession):
    fake = FakeRedis()
    monkeypatch.setattr(market_service, "get_redis", lambda: fake)

    q = MarketTrendsQuery(window=3)
    resp1 = await market_service.get_market_trends(db_session, q)
    assert resp1.cached is False
    assert any(k.startswith("market:trends:") for k in fake.store.keys())

    resp2 = await market_service.get_market_trends(db_session, q)
    assert resp2.cached is True
