"""Tests for refresh token system."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.services.user_service import UserService
from app.core.exceptions import AuthenticationError, TokenError
from app.models.user import User, RefreshToken


class TestRefreshTokenSystem:
    """Test refresh token functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_token_repo(self):
        """Create a mock token repository."""
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_db, mock_user_repo, mock_token_repo):
        """Create user service with mocked dependencies."""
        service = UserService(mock_db)
        service.user_repo = mock_user_repo
        service.token_repo = mock_token_repo
        return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = User()
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user

    @pytest.fixture
    def sample_refresh_token(self):
        """Create a sample refresh token for testing."""
        token = RefreshToken()
        token.id = 1
        token.user_id = 1
        token.token_hash = "hashed_token"
        token.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        token.revoked = False
        token.device_info = "test_device"
        token.token_family = "token_family_123"
        return token

    @pytest.mark.asyncio
    async def test_create_token_pair(self, user_service, sample_user):
        """Test creating access and refresh token pair."""
        access_token, refresh_token, token_hash, token_family, expires_at = user_service.create_token_pair(
            sample_user)

        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert isinstance(token_hash, str)
        assert isinstance(token_family, str)
        assert isinstance(expires_at, datetime)
        assert len(refresh_token) > 20  # Should be a secure random token

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, user_service, sample_user, sample_refresh_token):
        """Test successful access token refresh."""
        user_service.token_repo.get_by_token_hash.return_value = sample_refresh_token
        user_service.user_repo.get_by_id.return_value = sample_user
        user_service.token_repo.revoke_token_family.return_value = 1
        user_service.token_repo.create_refresh_token.return_value = sample_refresh_token

        result = await user_service.refresh_access_token("valid_refresh_token")

        assert result is not None
        assert len(result) == 2  # Should return (access_token, refresh_token)
        user_service.token_repo.revoke_token_family.assert_called_once()
        user_service.token_repo.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, user_service):
        """Test refresh with invalid token."""
        user_service.token_repo.get_by_token_hash.return_value = None

        result = await user_service.refresh_access_token("invalid_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_access_token_user_inactive(self, user_service, sample_refresh_token):
        """Test refresh with inactive user."""
        sample_user = User()
        sample_user.id = 1
        sample_user.is_active = False

        user_service.token_repo.get_by_token_hash.return_value = sample_refresh_token
        user_service.user_repo.get_by_id.return_value = sample_user

        result = await user_service.refresh_access_token("valid_token")

        assert result is None

    @pytest.mark.asyncio
    async def test_logout_user_success(self, user_service):
        """Test successful user logout."""
        user_service.token_repo.revoke_token.return_value = True

        result = await user_service.logout_user("valid_refresh_token")

        assert result is True
        user_service.token_repo.revoke_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_user_invalid_token(self, user_service):
        """Test logout with invalid token."""
        user_service.token_repo.revoke_token.return_value = False

        result = await user_service.logout_user("invalid_token")

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_tokens(self, user_service):
        """Test revoking all user tokens."""
        user_service.token_repo.revoke_all_user_tokens.return_value = 3

        result = await user_service.revoke_all_tokens(1)

        assert result == 3
        user_service.token_repo.revoke_all_user_tokens.assert_called_once_with(
            1)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service, sample_user):
        """Test successful user authentication."""
        user_service.user_repo.get_by_email.return_value = sample_user

        with patch('app.services.user_service.verify_password', return_value=True):
            result = await user_service.authenticate_user("test@example.com", "password")

        assert result == sample_user

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, user_service):
        """Test authentication with non-existent user."""
        user_service.user_repo.get_by_email.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await user_service.authenticate_user("nonexistent@example.com", "password")

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, user_service, sample_user):
        """Test authentication with inactive user."""
        sample_user.is_active = False
        user_service.user_repo.get_by_email.return_value = sample_user

        with pytest.raises(AuthenticationError, match="Account is deactivated"):
            await user_service.authenticate_user("test@example.com", "password")

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, user_service, sample_user):
        """Test authentication with wrong password."""
        user_service.user_repo.get_by_email.return_value = sample_user

        with patch('app.services.user_service.verify_password', return_value=False):
            with pytest.raises(AuthenticationError, match="Invalid email or password"):
                await user_service.authenticate_user("test@example.com", "wrong_password")
