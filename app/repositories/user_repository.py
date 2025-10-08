"""User repository for data access operations."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.user import User, UserProfile


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.get(User, user_id)
        return result

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email_verification_token(self, token: str) -> Optional[User]:
        """Get user by email verification token."""
        stmt = select(User).where(User.email_verification_token == token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()  # Flush to get ID without committing
        await self.db.refresh(user)
        return user

    async def update(self, user: User, user_data: dict) -> User:
        """Update user data."""
        for key, value in user_data.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.db.delete(user)
        await self.db.flush()

    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_profile(self, profile_data: dict) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(**profile_data)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def update_profile(
        self, profile: UserProfile, profile_data: dict
    ) -> UserProfile:
        """Update user profile data."""
        for key, value in profile_data.items():
            setattr(profile, key, value)
        await self.db.flush()
        return profile

    async def list_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List active users with pagination."""
        stmt = select(User).where(User.is_active.is_(True)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_users(self) -> int:
        """Count total number of users."""
        stmt = select(User)
        result = await self.db.execute(stmt)
        return len(list(result.scalars().all()))
