"""Email service for verification and notifications."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from ..repositories.user_repository import UserRepository
from ..core.exceptions import TokenError
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for email-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        # Mock email client for testing - in production this would be a real SMTP client
        self.email_client = None

    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return token_urlsafe(32)

    async def send_verification_email(self, user) -> bool:
        """Send email verification to user - minimal version."""
        try:
            logger.info(f"Starting email verification for user: {user.email}")

            # Check if email verification is enabled
            if hasattr(settings, "email") and hasattr(
                settings.email, "enable_email_verification"
            ):
                if not settings.email.enable_email_verification:
                    logger.info("Email verification is disabled, skipping email send")
                    return True

            # Check if user is already verified
            if user.is_verified:
                logger.info(
                    f"User {user.email} is already verified, skipping email send"
                )
                return True

            # Generate verification token
            token = self.generate_verification_token()
            logger.info(f"Generated token: {token}")

            # Update user with verification token
            await self.user_repo.update(
                user,
                {
                    "email_verification_token": token,
                    "email_verification_sent_at": datetime.now(timezone.utc),
                },
            )
            # Update the in-memory user object for tests
            setattr(user, "email_verification_token", token)
            setattr(user, "email_verification_sent_at", datetime.now(timezone.utc))
            logger.info("User updated with verification token")

            # Create verification URL
            verification_url = f"http://localhost:3001/verify-email?token={token}"
            logger.info(f"Verification URL: {verification_url}")

            # Send email if email client is available
            if self.email_client:
                email_sent = await self.email_client.send_email(
                    to=user.email,
                    subject="Verify Your Email - Qeem",
                    body=(f"click the link to verify your email: {verification_url}"),
                )
                if not email_sent:
                    logger.error(f"Failed to send verification email to {user.email}")
                    return False
            else:
                # For development, just log the details
                logger.info(f"Email verification setup completed for {user.email}")
                logger.info(f"Verification URL: {verification_url}")

            return True

        except Exception as e:
            logger.error(f"Error in send_verification_email: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def verify_email_token(self, token: str) -> Optional[User]:
        """Verify email token and mark user as verified."""
        try:
            logger.info(f"Verifying token: {token}")

            # Find user by verification token
            user = await self.user_repo.get_by_email_verification_token(token)
            if not user:
                logger.warning(f"No user found for token: {token}")
                raise TokenError("Invalid verification token")

            # Check if token is expired (24 hours)
            if user.email_verification_sent_at:
                token_age = datetime.now(timezone.utc) - user.email_verification_sent_at
                if token_age > timedelta(hours=24):
                    logger.warning(f"Token expired for user: {user.email}")
                    raise TokenError("Verification token has expired")

            # Mark user as verified
            await self.user_repo.update(
                user,
                {
                    "is_verified": True,
                    "email_verification_token": None,
                    "email_verification_sent_at": None,
                    "email_verified_at": datetime.now(timezone.utc),
                },
            )
            # Update the in-memory user object for tests
            setattr(user, "is_verified", True)
            setattr(user, "email_verification_token", None)
            setattr(user, "email_verification_sent_at", None)
            setattr(user, "email_verified_at", datetime.now(timezone.utc))

            logger.info(f"User {user.email} verified successfully")
            return user

        except TokenError:
            # Re-raise TokenError as-is
            raise
        except Exception as e:
            logger.error(f"Error verifying email token: {e}")
            raise TokenError("Invalid verification token")

    async def resend_verification_email(self, user) -> bool:
        """Resend verification email to user."""
        if user.is_verified:
            logger.warning(f"User {user.email} is already verified")
            return False

        return await self.send_verification_email(user)
