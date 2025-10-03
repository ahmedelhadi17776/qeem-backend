"""Market statistics model for ML data."""

from sqlalchemy import Column, String, Float, Integer, Date, JSON
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, IDMixin, TimestampMixin


class MarketStatistics(Base, IDMixin, TimestampMixin):
    """Market statistics aggregated from scraped data."""

    __tablename__ = "market_statistics"

    # Time Period
    date = Column(Date, nullable=False, index=True)
    period_type = Column(
        String(20), default="weekly", nullable=False
    )  # daily, weekly, monthly

    # Market Segment
    project_type = Column(String(50), nullable=False, index=True)
    experience_level = Column(String(20), nullable=False)  # junior, mid, senior
    location = Column(String(100), nullable=False, index=True)

    # Statistics
    average_rate = Column(Float, nullable=False)
    median_rate = Column(Float, nullable=False)
    min_rate = Column(Float, nullable=False)
    max_rate = Column(Float, nullable=False)
    rate_std_dev = Column(Float, nullable=True)

    # Sample Information
    sample_size = Column(Integer, nullable=False)
    # upwork, freelancer, etc.
    data_source = Column(String(100), nullable=False)

    # Additional Metrics
    demand_score = Column(Float, nullable=True)  # 0-1 scale
    competition_score = Column(Float, nullable=True)  # 0-1 scale
    # rising, stable, declining
    market_trend = Column(String(20), nullable=True)

    # Raw Data Reference: JSON on SQLite, JSONB on Postgres
    raw_data_ids = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
