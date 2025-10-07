"""Email service for sending verification emails and managing email verification."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from secrets import token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..infra.email import get_email_client, render_email_template
from ..models.user import User
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Service for email-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.email_client = get_email_client()
    
    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return token_urlsafe(32)
    
    async def send_verification_email(self, user: User) -> bool:
        """Send email verification to user.
        
        Args:
            user: User object to send verification to
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Generate verification token
            token = self.generate_verification_token()
            
            # Update user with verification token
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.utcnow()
            await self.db.flush()
            
            # Create verification URL
            verification_url = f"{settings.cors_origins[0] if settings.cors_origins else 'http://localhost:3000'}/verify-email?token={token}"
            
            # Render email template
            context = {
                "verification_url": verification_url,
                "user_name": user.profile.first_name if user.profile else "User",
                "expires_in_hours": settings.email.verification_token_ttl_hours
            }
            
            html_content, text_content = render_email_template("verification", context)
            
            # Send email
            success = await self.email_client.send_email(
                to_email=user.email,
                subject="Verify Your Email - Qeem",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"Verification email sent to {user.email}")
            else:
                logger.error(f"Failed to send verification email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {e}")
            return False
    
    async def verify_email_token(self, token: str) -> Optional[User]:
        """Verify email token and mark user as verified.
        
        Args:
            token: Verification token
            
        Returns:
            User object if verification successful, None otherwise
        """
        try:
            # Find user by token
            user = await self.user_repo.get_by_email_verification_token(token)
            if not user:
                logger.warning(f"Invalid verification token: {token}")
                return None
            
            # Check if token is expired
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(
                    hours=settings.email.verification_token_ttl_hours
                )
                if datetime.utcnow() > expiry_time:
                    logger.warning(f"Expired verification token for user {user.email}")
                    return None
            
            # Mark user as verified
            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            user.email_verification_token = None  # Clear token
            await self.db.flush()
            
            logger.info(f"Email verified successfully for user {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error verifying email token: {e}")
            return None
    
    async def resend_verification_email(self, user: User) -> bool:
        """Resend verification email to user.
        
        Args:
            user: User object to resend verification to
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if user.is_verified:
            logger.warning(f"User {user.email} is already verified")
            return False
        
        # Check rate limiting (prevent spam)
        if user.email_verification_sent_at:
            time_since_last = datetime.utcnow() - user.email_verification_sent_at
            if time_since_last.total_seconds() < 300:  # 5 minutes
                logger.warning(f"Verification email sent too recently for {user.email}")
                return False
        
        return await self.send_verification_email(user)
    
    async def is_verification_token_valid(self, token: str) -> bool:
        """Check if verification token is valid and not expired.
        
        Args:
            token: Verification token to check
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            user = await self.user_repo.get_by_email_verification_token(token)
            if not user:
                return False
            
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(
                    hours=settings.email.verification_token_ttl_hours
                )
                return datetime.utcnow() <= expiry_time
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking verification token: {e}")
            return False
