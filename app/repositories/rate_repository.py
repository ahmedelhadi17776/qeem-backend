"""Rate calculation repository for data access operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models.rate_calculation import RateCalculation


class RateRepository:
    """Repository for rate calculation-related database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, calculation_id: int) -> Optional[RateCalculation]:
        """Get rate calculation by ID."""
        result = await self.db.get(RateCalculation, calculation_id)
        return result

    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[RateCalculation]:
        """Get rate calculations for a specific user with pagination."""
        stmt = (
            select(RateCalculation)
            .where(RateCalculation.user_id == user_id)
            .order_by(desc(RateCalculation.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, calculation_data: dict) -> RateCalculation:
        """Create a new rate calculation."""
        calculation = RateCalculation(**calculation_data)
        self.db.add(calculation)
        await self.db.flush()
        await self.db.refresh(calculation)
        return calculation

    async def update(
        self, calculation: RateCalculation, calculation_data: dict
    ) -> RateCalculation:
        """Update rate calculation data."""
        for key, value in calculation_data.items():
            setattr(calculation, key, value)
        await self.db.flush()
        await self.db.refresh(calculation)
        return calculation

    async def delete(self, calculation: RateCalculation) -> None:
        """Delete rate calculation."""
        await self.db.delete(calculation)
        await self.db.flush()

    async def get_favorites(self, user_id: int) -> List[RateCalculation]:
        """Get favorite rate calculations for a user."""
        stmt = (
            select(RateCalculation)
            .where(
                RateCalculation.user_id == user_id,
                RateCalculation.is_favorite.is_(True),
            )
            .order_by(desc(RateCalculation.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_favorite(
        self, calculation_id: int, user_id: int, is_favorite: bool
    ) -> Optional[RateCalculation]:
        """Set/unset a rate calculation as favorite."""
        calculation = await self.get_by_id(calculation_id)
        if calculation and calculation.user_id == user_id:
            calculation.is_favorite = is_favorite  # type: ignore[assignment]
            await self.db.flush()
            await self.db.refresh(calculation)
            return calculation
        return None

    async def get_by_project_type(
        self, project_type: str, skip: int = 0, limit: int = 100
    ) -> List[RateCalculation]:
        """Get rate calculations by project type."""
        stmt = (
            select(RateCalculation)
            .where(RateCalculation.project_type == project_type)
            .order_by(desc(RateCalculation.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """Count rate calculations for a user."""
        stmt = select(RateCalculation).where(RateCalculation.user_id == user_id)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))

    async def get_recent_calculations(self, limit: int = 10) -> List[RateCalculation]:
        """Get recent rate calculations across all users."""
        stmt = (
            select(RateCalculation)
            .order_by(desc(RateCalculation.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
