from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...schemas.market import (
    MarketStatisticsQuery,
    MarketStatisticsResponse,
    MarketTrendsQuery,
    MarketTrendsResponse,
)
from ...services.market import get_market_statistics, get_market_trends


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/statistics", response_model=MarketStatisticsResponse)
async def statistics(
    query: MarketStatisticsQuery = Depends(), db: Session = Depends(get_db)
) -> MarketStatisticsResponse:
    return get_market_statistics(db, query)


@router.get("/trends", response_model=MarketTrendsResponse)
async def trends(
    query: MarketTrendsQuery = Depends(), db: Session = Depends(get_db)
) -> MarketTrendsResponse:
    return get_market_trends(db, query)
