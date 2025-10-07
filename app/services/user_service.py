"""User service for authentication and profile management."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import hash_password, verify_password, create_access_token
from ..models.user import User, UserProfile
from ..repositories.user_repository import UserRepository
from ..schemas.auth import UserRegisterRequest, UserProfileUpdateRequest


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_user(self, user_data: UserRegisterRequest) -> User:
        """Create a new user with profile.

        Args:
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user_create_data = {
            "email": user_data.email,
            "password_hash": hashed_password,
            "is_active": True,
            "is_verified": False,  # TODO: Add email verification
        }

        user = await self.user_repo.create(user_create_data)

        # Create user profile
        profile_data = {
            "user_id": user.id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "country": "Egypt",  # Default for Egyptian freelancers
            "preferred_currency": "EGP",
        }

        await self.user_repo.create_profile(profile_data)

        # Ensure all user attributes are loaded before returning
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, str(user.password_hash)):
            return None

        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User object if found, None otherwise
        """
        return await self.user_repo.get_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object if found, None otherwise
        """
        return await self.user_repo.get_by_id(user_id)

    async def get_user_with_profile(
        self, user_id: int
    ) -> Optional[tuple[User, UserProfile]]:
        """Get user with their profile.

        Args:
            user_id: User ID

        Returns:
            Tuple of (User, UserProfile) if found, None otherwise
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        profile = await self.user_repo.get_profile(user_id)
        if profile is None:
            return None
        return user, profile

    async def update_user_profile(
        self, user_id: int, profile_data: UserProfileUpdateRequest
    ) -> Optional[UserProfile]:
        """Update user profile.

        Args:
            user_id: User ID
            profile_data: Profile update data

        Returns:
            Updated profile object if successful, None otherwise
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # Get existing profile or create new one
        profile = await self.user_repo.get_profile(user_id)

        # Convert Pydantic model to dict, excluding None values
        update_data = {
            k: v for k, v in profile_data.model_dump().items() if v is not None
        }

        if profile:
            # Update existing profile
            return await self.user_repo.update_profile(profile, update_data)
        else:
            # Create new profile
            update_data["user_id"] = user_id
            return await self.user_repo.create_profile(update_data)

    def create_access_token_for_user(self, user: User) -> str:
        """Create JWT access token for user.

        Args:
            user: User object

        Returns:
            JWT token string
        """
        return create_access_token(
            subject=str(user.id), extra_claims={"email": user.email}
        )

    async def is_email_available(self, email: str) -> bool:
        """Check if email is available for registration.

        Args:
            email: Email to check

        Returns:
            True if email is available, False otherwise
        """
        user = await self.user_repo.get_by_email(email)
        return user is None
