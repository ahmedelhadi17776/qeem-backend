"""Repository for market statistics queries."""

from datetime import date
from typing import List, Optional, Tuple, cast
from datetime import date as DateType

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.orm import Session

from ..models.market_statistics import MarketStatistics


class MarketRepository:
    """Data access for market statistics."""

    def __init__(self, db: Session):
        self.db = db

    def _apply_filters(
        self,
        stmt: Select,
        *,
        project_type: Optional[str],
        location: Optional[str],
        period_type: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> Select:
        conditions = []
        if project_type:
            conditions.append(MarketStatistics.project_type == project_type)
        if location:
            conditions.append(MarketStatistics.location == location)
        if period_type:
            conditions.append(MarketStatistics.period_type == period_type)
        if date_from:
            conditions.append(MarketStatistics.date >= date_from)
        if date_to:
            conditions.append(MarketStatistics.date <= date_to)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt

    def list_statistics(
        self,
        *,
        project_type: Optional[str],
        location: Optional[str],
        period_type: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        limit: int,
        offset: int,
    ) -> Tuple[List[MarketStatistics], int]:
        """Return paginated statistics and total count."""
        base_stmt = select(MarketStatistics)
        base_stmt = self._apply_filters(
            base_stmt,
            project_type=project_type,
            location=location,
            period_type=period_type,
            date_from=date_from,
            date_to=date_to,
        ).order_by(desc(MarketStatistics.date))

        total_stmt = select(func.count()).select_from(
            self._apply_filters(
                select(MarketStatistics),
                project_type=project_type,
                location=location,
                period_type=period_type,
                date_from=date_from,
                date_to=date_to,
            ).subquery()
        )

        items = list(
            self.db.execute(base_stmt.offset(offset).limit(limit)).scalars().all()
        )
        total = int(self.db.execute(total_stmt).scalar() or 0)
        return items, total

    def list_trends(
        self,
        *,
        project_type: Optional[str],
        location: Optional[str],
        period_type: Optional[str],
        window: int,
    ) -> List[MarketStatistics]:
        """Return last N periods for trends (ordered ascending by date)."""
        stmt = select(MarketStatistics)
        stmt = (
            self._apply_filters(
                stmt,
                project_type=project_type,
                location=location,
                period_type=period_type,
                date_from=None,
                date_to=None,
            )
            .order_by(desc(MarketStatistics.date))
            .limit(window)
        )

        rows = list(self.db.execute(stmt).scalars().all())
        # Help type checker understand attribute type
        rows.sort(key=lambda r: cast(DateType, r.date))
        return rows
