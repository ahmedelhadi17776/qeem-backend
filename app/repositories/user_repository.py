"""User repository for data access operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.user import User, UserProfile


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_data: dict) -> User:
        """Update user data."""
        for key, value in user_data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Delete user."""
        self.db.delete(user)
        self.db.commit()

    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_profile(self, profile_data: dict) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(**profile_data)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_profile(self, profile: UserProfile, profile_data: dict) -> UserProfile:
        """Update user profile data."""
        for key, value in profile_data.items():
            setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List active users with pagination."""
        stmt = select(User).where(User.is_active.is_(True)).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_users(self) -> int:
        """Count total number of users."""
        stmt = select(User)
        return len(list(self.db.execute(stmt).scalars().all()))
