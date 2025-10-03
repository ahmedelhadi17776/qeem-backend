"""Rate calculation repository for data access operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from ..models.rate_calculation import RateCalculation


class RateRepository:
    """Repository for rate calculation-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, calculation_id: int) -> Optional[RateCalculation]:
        """Get rate calculation by ID."""
        return self.db.get(RateCalculation, calculation_id)

    def get_by_user_id(
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
        return list(self.db.execute(stmt).scalars().all())

    def create(self, calculation_data: dict) -> RateCalculation:
        """Create a new rate calculation."""
        calculation = RateCalculation(**calculation_data)
        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def update(
        self, calculation: RateCalculation, calculation_data: dict
    ) -> RateCalculation:
        """Update rate calculation data."""
        for key, value in calculation_data.items():
            setattr(calculation, key, value)
        self.db.commit()
        self.db.refresh(calculation)
        return calculation

    def delete(self, calculation: RateCalculation) -> None:
        """Delete rate calculation."""
        self.db.delete(calculation)
        self.db.commit()

    def get_favorites(self, user_id: int) -> List[RateCalculation]:
        """Get favorite rate calculations for a user."""
        stmt = (
            select(RateCalculation)
            .where(
                RateCalculation.user_id == user_id,
                RateCalculation.is_favorite.is_(True),
            )
            .order_by(desc(RateCalculation.created_at))
        )
        return list(self.db.execute(stmt).scalars().all())

    def set_favorite(
        self, calculation_id: int, user_id: int, is_favorite: bool
    ) -> Optional[RateCalculation]:
        """Set/unset a rate calculation as favorite."""
        calculation = self.get_by_id(calculation_id)
        if calculation and calculation.user_id == user_id:
            calculation.is_favorite = is_favorite  # type: ignore[assignment]
            self.db.commit()
            self.db.refresh(calculation)
            return calculation
        return None

    def get_by_project_type(
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
        return list(self.db.execute(stmt).scalars().all())

    def count_by_user(self, user_id: int) -> int:
        """Count rate calculations for a user."""
        stmt = select(RateCalculation).where(RateCalculation.user_id == user_id)
        return len(list(self.db.execute(stmt).scalars().all()))

    def get_recent_calculations(self, limit: int = 10) -> List[RateCalculation]:
        """Get recent rate calculations across all users."""
        stmt = (
            select(RateCalculation)
            .order_by(desc(RateCalculation.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
