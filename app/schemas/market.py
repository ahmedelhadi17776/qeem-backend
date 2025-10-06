"""Schemas for market statistics and trends endpoints."""

from datetime import date
from typing import Literal, Optional, List

from pydantic import BaseModel, Field


class MarketStatisticsQuery(BaseModel):
    """Query parameters for statistics endpoint."""

    project_type: Optional[str] = Field(default=None, description="Project type filter")
    location: Optional[str] = Field(default=None, description="Location filter")
    period_type: Literal["daily", "weekly", "monthly"] = Field(
        default="weekly", description="Aggregation period type"
    )
    date_from: Optional[date] = Field(default=None, description="Start date inclusive")
    date_to: Optional[date] = Field(default=None, description="End date inclusive")
    limit: int = Field(default=20, ge=1, le=100, description="Page size")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class MarketStatisticsItem(BaseModel):
    date: date
    period_type: Literal["daily", "weekly", "monthly"]
    project_type: str
    location: str
    average_rate: float
    median_rate: float
    min_rate: float
    max_rate: float
    demand_score: Optional[float] = None
    competition_score: Optional[float] = None
    market_trend: Optional[str] = None


class MarketStatisticsResponse(BaseModel):
    items: List[MarketStatisticsItem] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0
    cached: bool = False


class MarketTrendsQuery(BaseModel):
    """Query parameters for trends endpoint."""

    project_type: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    period_type: Literal["daily", "weekly", "monthly"] = "weekly"
    window: int = Field(default=12, ge=1, le=52, description="Number of periods")


class MarketTrendsPoint(BaseModel):
    period_start: date
    period_end: Optional[date] = None
    average_rate: float
    median_rate: float
    demand_score: Optional[float] = None
    market_trend: Optional[str] = None


class MarketTrendsResponse(BaseModel):
    points: List[MarketTrendsPoint] = Field(default_factory=list)
    cached: bool = False
