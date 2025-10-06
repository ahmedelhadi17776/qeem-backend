from datetime import date

from sqlalchemy.orm import Session

from app.schemas.market import MarketStatisticsQuery, MarketTrendsQuery
from app.services.market import get_market_statistics, get_market_trends


def test_market_statistics_empty(db_session: Session, monkeypatch):
    query = MarketStatisticsQuery(limit=5, offset=0)
    resp = get_market_statistics(db_session, query)
    assert resp.limit == 5
    assert resp.offset == 0
    assert isinstance(resp.items, list)


def test_market_trends_empty(db_session: Session):
    query = MarketTrendsQuery(window=5)
    resp = get_market_trends(db_session, query)
    assert len(resp.points) <= 5
