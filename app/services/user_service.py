"""User service for authentication and profile management."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_transaction_manager
from ..core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    create_token_family,
)
from ..models.user import User, UserProfile
from ..repositories.user_repository import UserRepository
from ..repositories.token_repository import TokenRepository
from ..schemas.auth import UserRegisterRequest, UserProfileUpdateRequest
from ..services.email_service import EmailService
from ..infra.metrics import record_user_registration, record_user_login
from ..services.audit_service import AuditService
from ..core.exceptions import ValidationError, AuthenticationError


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)
        self.audit_service = AuditService(db)

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
            raise ValidationError(
                "Email already registered", details={"email": user_data.email}
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Use transaction to ensure atomicity
        # Check if we're already in a transaction
        if self.db.in_transaction():
            # Already in transaction, just create user directly
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
            }

            profile = await self.user_repo.create_profile(profile_data)
            user.profile = profile

            # Record audit log
            await self.audit_service.log_action(
                user_id=user.id,
                action="user_registration",
                resource_type="user",
                resource_id=str(user.id),
                new_values={"email": user_data.email},
            )

            # Record metrics
            record_user_registration()

            return user
        else:
            # Not in transaction, use transaction manager
            async with get_transaction_manager(self.db):
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

                profile = await self.user_repo.create_profile(profile_data)
                user.profile = profile

                # Record audit log
                await self.audit_service.log_action(
                    user_id=user.id,
                    action="user_registration",
                    resource_type="user",
                    resource_id=str(user.id),
                    new_values={"email": user_data.email},
                )

                # Record metrics
                record_user_registration()

                # Send verification email
                email_service = EmailService(self.db)
                await email_service.send_verification_email(user)

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
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        if not verify_password(password, str(user.password_hash)):
            raise AuthenticationError("Invalid email or password")

        # Record metrics
        record_user_login("email")

        # Log audit trail
        self.audit_service.log_action_async(
            user_id=user.id,
            action="user_login",
            resource_type="user",
            resource_id=str(user.id),
            success=True,
        )

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

        # Use transaction to ensure atomicity
        # Check if we're already in a transaction
        if self.db.in_transaction():
            # Already in transaction, just update profile directly
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
        else:
            # Not in transaction, use transaction manager
            async with get_transaction_manager(self.db):
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

    def create_token_pair(
        self, user: User, device_info: Optional[str] = None
    ) -> tuple[str, str]:
        """Create access and refresh token pair.

        Args:
            user: User object
            device_info: Device information (user agent, IP, etc.)

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create access token
        access_token = create_access_token(
            subject=str(user.id), extra_claims={"email": user.email}
        )

        # Create refresh token
        refresh_token = create_refresh_token()
        token_hash = hash_refresh_token(refresh_token)
        token_family = create_token_family()

        # Store refresh token in database
        from datetime import datetime, timedelta, timezone

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Note: We'll store the token in the calling method to handle
        # transactions properly
        return access_token, refresh_token, token_hash, token_family, expires_at

    async def refresh_access_token(
        self, refresh_token: str
    ) -> Optional[tuple[str, str]]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            Tuple of (new_access_token, new_refresh_token) if successful, None otherwise
        """
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self.token_repo.get_by_token_hash(token_hash)

        if not stored_token:
            return None

        # Get user
        user = await self.user_repo.get_by_id(stored_token.user_id)
        if not user or not user.is_active:
            return None

        # Revoke old token family (token rotation)
        if stored_token.token_family:
            await self.token_repo.revoke_token_family(stored_token.token_family)

        # Create new token pair
        (
            access_token,
            new_refresh_token,
            new_token_hash,
            new_token_family,
            expires_at,
        ) = self.create_token_pair(user, stored_token.device_info)

        # Store new refresh token
        await self.token_repo.create_refresh_token(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            device_info=stored_token.device_info,
            token_family=new_token_family,
        )

        return access_token, new_refresh_token

    async def revoke_all_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        return await self.token_repo.revoke_all_user_tokens(user_id)

    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token.

        Args:
            refresh_token: Refresh token to revoke

        Returns:
            True if token revoked successfully, False otherwise
        """
        token_hash = hash_refresh_token(refresh_token)
        return await self.token_repo.revoke_token(token_hash)
