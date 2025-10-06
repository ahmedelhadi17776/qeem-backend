"""Repository tests for market statistics queries."""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.market_statistics import MarketStatistics
from app.repositories.market_repository import MarketRepository


def _seed_stats(db: Session, days: int = 5, project_type: str = "web_development", location: str = "Cairo"):
    base = date(2024, 1, 1)
    for i in range(days):
        row = MarketStatistics(
            date=base + timedelta(days=i * 7),
            period_type="weekly",
            project_type=project_type,
            experience_level="mid",
            location=location,
            average_rate=70 + i,
            median_rate=68 + i,
            min_rate=50,
            max_rate=100,
            sample_size=100 + i,
            data_source="seed",
        )
        db.add(row)
    db.flush()


def test_market_repository_filters_and_trends(db_session: Session):
    repo = MarketRepository(db_session)
    _seed_stats(db_session, days=6)

    # list_statistics with pagination
    items, total = repo.list_statistics(
        project_type="web_development",
        location="Cairo",
        period_type="weekly",
        date_from=None,
        date_to=None,
        limit=3,
        offset=0,
    )
    assert total == 6
    assert len(items) == 3

    # list_trends window ordering asc
    rows = repo.list_trends(
        project_type="web_development",
        location="Cairo",
        period_type="weekly",
        window=4,
    )
    assert len(rows) == 4
    assert rows[0].date < rows[-1].date
