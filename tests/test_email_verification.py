"""Tests for email verification system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.services.email_service import EmailService
from app.core.exceptions import TokenError, EmailError
from app.models.user import User


class TestEmailService:
    """Test email service functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_email_client(self):
        """Create a mock email client."""
        client = AsyncMock()
        client.send_email = AsyncMock(
            return_value=True)  # Return True by default
        return client

    @pytest.fixture
    def email_service(self, mock_db, mock_user_repo, mock_email_client):
        """Create email service with mocked dependencies."""
        service = EmailService(mock_db)
        service.user_repo = mock_user_repo
        service.email_client = mock_email_client
        return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.is_verified = False
        user.email_verification_token = None
        user.email_verification_sent_at = None
        return user

    @pytest.mark.asyncio
    async def test_generate_verification_token(self, email_service):
        """Test verification token generation."""
        token = email_service.generate_verification_token()

        assert isinstance(token, str)
        assert len(token) > 20  # Should be a secure random token

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, email_service, sample_user):
        """Test successful verification email sending."""
        email_service.email_client.send_email.return_value = True

        result = await email_service.send_verification_email(sample_user)

        assert result is True
        email_service.email_client.send_email.assert_called_once()
        assert sample_user.email_verification_token is not None
        assert sample_user.email_verification_sent_at is not None

    @pytest.mark.asyncio
    async def test_send_verification_email_failure(self, email_service, sample_user):
        """Test verification email sending failure."""
        email_service.email_client.send_email.return_value = False

        result = await email_service.send_verification_email(sample_user)

        assert result is False
        email_service.email_client.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_already_verified(self, email_service, sample_user):
        """Test sending verification email to already verified user."""
        sample_user.is_verified = True

        result = await email_service.send_verification_email(sample_user)

        assert result is True
        email_service.email_client.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_token_success(self, email_service, sample_user):
        """Test successful email verification."""
        sample_user.email_verification_token = "valid_token"
        sample_user.email_verification_sent_at = datetime.now(timezone.utc)
        email_service.user_repo.get_by_email_verification_token.return_value = sample_user

        result = await email_service.verify_email_token("valid_token")

        assert result == sample_user
        assert sample_user.is_verified is True
        assert sample_user.email_verified_at is not None
        assert sample_user.email_verification_token is None

    @pytest.mark.asyncio
    async def test_verify_email_token_invalid(self, email_service):
        """Test email verification with invalid token."""
        email_service.user_repo.get_by_email_verification_token.return_value = None

        with pytest.raises(TokenError, match="Invalid verification token"):
            await email_service.verify_email_token("invalid_token")

    @pytest.mark.asyncio
    async def test_verify_email_token_expired(self, email_service, sample_user):
        """Test email verification with expired token."""
        sample_user.email_verification_token = "expired_token"
        sample_user.email_verification_sent_at = datetime.now(timezone.utc) - \
            timedelta(hours=25)  # Expired
        email_service.user_repo.get_by_email_verification_token.return_value = sample_user

        with pytest.raises(TokenError, match="Verification token has expired"):
            await email_service.verify_email_token("expired_token")

    @pytest.mark.asyncio
    async def test_resend_verification_email(self, email_service, sample_user):
        """Test resending verification email."""
        email_service.email_client.send_email.return_value = True

        result = await email_service.resend_verification_email(sample_user)

        assert result is True
        email_service.email_client.send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_resend_verification_email_already_verified(self, email_service, sample_user):
        """Test resending verification email to already verified user."""
        sample_user.is_verified = True

        result = await email_service.resend_verification_email(sample_user)

        assert result is False
        email_service.email_client.send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.email_service.settings')
    async def test_send_verification_email_disabled(self, mock_settings, email_service, sample_user):
        """Test sending verification email when disabled."""
        mock_settings.email.enable_email_verification = False

        result = await email_service.send_verification_email(sample_user)

        assert result is True
        email_service.email_client.send_email.assert_not_called()
