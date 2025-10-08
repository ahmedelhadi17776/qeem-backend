"""Market service with cache-aside using Redis."""

import hashlib
import json
from typing import Dict, List, Optional, cast
from datetime import date as DateType

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.redis import get_redis
from ..models.market_statistics import MarketStatistics
from ..schemas.market import (
    MarketStatisticsItem,
    MarketStatisticsQuery,
    MarketStatisticsResponse,
    MarketTrendsPoint,
    MarketTrendsQuery,
    MarketTrendsResponse,
)
from ..repositories.market_repository import MarketRepository
from ..core.config import get_settings
import logging

logger = logging.getLogger(__name__)


def _stable_key(prefix: str, payload: Dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    # Non-security hashing for cache key; use SHA-256 to satisfy security scanners
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{prefix}:{digest}"


def _redis_get_safe(key: str) -> Optional[str]:
    try:
        r = get_redis()
        if r is None:
            return None
        value = r.get(key)
        return cast(Optional[str], value)
    except Exception as exc:  # pragma: no cover - network/environmental
        logger.warning("market_cache_get_failed", extra={"key": key, "err": str(exc)})
        return None


def _redis_setex_safe(key: str, ttl: int, payload: str) -> None:
    try:
        r = get_redis()
        if r is None:
            return
        r.setex(key, ttl, payload)
    except Exception as exc:  # pragma: no cover - network/environmental
        logger.warning(
            "market_cache_set_failed", extra={"key": key, "ttl": ttl, "err": str(exc)}
        )


def _serialize_item(row: MarketStatistics) -> MarketStatisticsItem:
    return MarketStatisticsItem(
        date=cast(DateType, row.date),
        period_type=row.period_type,  # type: ignore[arg-type]
        project_type=cast(str, row.project_type),
        location=cast(str, row.location),
        average_rate=float(row.average_rate),
        median_rate=float(row.median_rate),
        min_rate=float(row.min_rate),
        max_rate=float(row.max_rate),
        demand_score=float(row.demand_score) if row.demand_score is not None else None,
        competition_score=(
            float(row.competition_score) if row.competition_score is not None else None
        ),
        market_trend=cast(Optional[str], row.market_trend),
    )


async def get_market_statistics(
    db: AsyncSession, query: MarketStatisticsQuery
) -> MarketStatisticsResponse:
    """Return paginated statistics, using cache-aside."""
    settings = get_settings()
    cache_ttl = int(
        getattr(settings, "market_cache_ttl", 3600)
        if hasattr(settings, "market_cache_ttl")
        else 3600
    )
    key = _stable_key("market:stats", query.model_dump())
    cached = _redis_get_safe(key)
    if cached:
        data = json.loads(cached)
        logger.info("market_statistics_cache_hit", extra={"key": key})
        resp = MarketStatisticsResponse.model_validate(data)
        resp.cached = True
        return resp

    repo = MarketRepository(db)
    rows, total = await repo.list_statistics(
        project_type=query.project_type,
        location=query.location,
        period_type=query.period_type,
        date_from=query.date_from,
        date_to=query.date_to,
        limit=query.limit,
        offset=query.offset,
    )

    items = [_serialize_item(r) for r in rows]
    response = MarketStatisticsResponse(
        items=items, total=total, limit=query.limit, offset=query.offset, cached=False
    )
    _redis_setex_safe(key, cache_ttl, response.model_dump_json())
    logger.info(
        "market_statistics_cache_store",
        extra={"key": key, "ttl": cache_ttl, "count": len(items)},
    )
    return response


async def get_market_trends(
    db: AsyncSession, query: MarketTrendsQuery
) -> MarketTrendsResponse:
    """Return trend points for last N periods, using cache-aside."""
    settings = get_settings()
    cache_ttl = int(
        getattr(settings, "market_cache_ttl", 3600)
        if hasattr(settings, "market_cache_ttl")
        else 3600
    )
    key = _stable_key("market:trends", query.model_dump())
    cached = _redis_get_safe(key)
    if cached:
        data = json.loads(cached)
        logger.info("market_trends_cache_hit", extra={"key": key})
        resp = MarketTrendsResponse.model_validate(data)
        resp.cached = True
        return resp

    repo = MarketRepository(db)
    rows = await repo.list_trends(
        project_type=query.project_type,
        location=query.location,
        period_type=query.period_type,
        window=query.window,
    )

    points: List[MarketTrendsPoint] = []
    for r in rows:
        points.append(
            MarketTrendsPoint(
                period_start=cast(DateType, r.date),
                period_end=None,
                average_rate=float(r.average_rate),
                median_rate=float(r.median_rate),
                demand_score=(
                    float(r.demand_score) if r.demand_score is not None else None
                ),
                market_trend=cast(Optional[str], r.market_trend),
            )
        )

    response = MarketTrendsResponse(points=points, cached=False)
    _redis_setex_safe(key, cache_ttl, response.model_dump_json())
    logger.info(
        "market_trends_cache_store",
        extra={"key": key, "ttl": cache_ttl, "points": len(points)},
    )
    return response
