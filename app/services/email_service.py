"""Minimal email service for testing."""

import logging
from datetime import datetime, timezone
from typing import Optional
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EmailService:
    """Minimal service for email-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return token_urlsafe(32)

    async def send_verification_email(self, user) -> bool:
        """Send email verification to user - minimal version."""
        try:
            logger.info(f"Starting email verification for user: {user.email}")

            # Generate verification token
            token = self.generate_verification_token()
            logger.info(f"Generated token: {token}")

            # Update user with verification token
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.info("User updated with verification token")

            # Create verification URL
            verification_url = f"http://localhost:3000/verify-email?token={token}"
            logger.info(f"Verification URL: {verification_url}")

            # For now, just log the verification details and return success
            logger.info(f"Email verification setup completed for {user.email}")
            return True

        except Exception as e:
            logger.error(f"Error in send_verification_email: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def verify_email_token(self, token: str) -> Optional[object]:
        """Verify email token and mark user as verified."""
        try:
            logger.info(f"Verifying token: {token}")
            # For now, just return None to indicate invalid token
            return None

        except Exception as e:
            logger.error(f"Error verifying email token: {e}")
            return None

    async def resend_verification_email(self, user) -> bool:
        """Resend verification email to user."""
        if user.is_verified:
            logger.warning(f"User {user.email} is already verified")
            return False

        return await self.send_verification_email(user)
