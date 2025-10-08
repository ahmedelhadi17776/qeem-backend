"""Simple tests for token repository."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from app.repositories.token_repository import TokenRepository


class TestTokenRepository:
    """Test TokenRepository basic functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def token_repo(self, mock_db_session):
        """Create TokenRepository instance."""
        return TokenRepository(mock_db_session)

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, token_repo, mock_db_session):
        """Test creating a refresh token."""
        # Setup
        user_id = 1
        token_hash = "test_hash"
        expires_at = datetime.now(timezone.utc)
        device_info = "Test Device"

        # Mock the refresh token creation
        mock_token = Mock()
        mock_token.id = 1
        mock_token.user_id = user_id
        mock_token.token_hash = token_hash
        mock_token.expires_at = expires_at
        mock_token.device_info = device_info

        with patch('app.repositories.token_repository.RefreshToken', return_value=mock_token):
            with patch.object(token_repo, '_store_in_redis', new_callable=AsyncMock):
                # Test
                result = await token_repo.create_refresh_token(
                    user_id=user_id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    device_info=device_info
                )

                # Assert
                assert result == mock_token
                mock_db_session.add.assert_called_once()
                mock_db_session.flush.assert_called_once()
                mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_token_hash(self, token_repo, mock_db_session):
        """Test getting refresh token by hash."""
        # Setup
        token_hash = "test_hash"
        mock_token = Mock()
        mock_token.token_hash = token_hash

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_token
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await token_repo.get_by_token_hash(token_hash)

        # Assert
        assert result == mock_token
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_token_hash_not_found(self, token_repo, mock_db_session):
        """Test getting refresh token by hash when not found."""
        # Setup
        token_hash = "nonexistent_hash"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await token_repo.get_by_token_hash(token_hash)

        # Assert
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_token_by_hash(self, token_repo, mock_db_session):
        """Test revoking a token by hash."""
        # Setup
        token_hash = "test_hash"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = Mock()
        mock_db_session.execute.return_value = mock_result

        with patch.object(token_repo, '_remove_from_redis', new_callable=AsyncMock):
            # Test
            result = await token_repo.revoke_token(token_hash)

            # Assert
            assert result is True
            # Should be called twice: once for get_by_token_hash, once for update
            assert mock_db_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_revoke_token_not_found(self, token_repo, mock_db_session):
        """Test revoking a token that doesn't exist."""
        # Setup
        token_hash = "nonexistent_hash"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await token_repo.revoke_token(token_hash)

        # Assert
        assert result is False
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_active_tokens(self, token_repo, mock_db_session):
        """Test getting all active tokens for a user."""
        # Setup
        user_id = 1
        mock_tokens = [Mock(), Mock()]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_tokens
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await token_repo.get_user_active_tokens(user_id)

        # Assert
        assert result == mock_tokens
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, token_repo, mock_db_session):
        """Test revoking all tokens for a user."""
        # Setup
        user_id = 1

        # Mock the select query result
        mock_select_result = Mock()
        mock_select_result.all.return_value = [(1, "hash1"), (2, "hash2")]

        # Mock the update query results (one per token)
        mock_update_result = Mock()
        mock_update_result.rowcount = 1

        # Configure mock to return different results based on call
        mock_db_session.execute.side_effect = [
            mock_select_result,  # Select query
            mock_update_result,   # Update query for token 1
            mock_update_result    # Update query for token 2
        ]

        with patch.object(token_repo, '_remove_from_redis', new_callable=AsyncMock):
            # Test
            result = await token_repo.revoke_all_user_tokens(user_id)

            # Assert
            assert result == 2  # Should revoke 2 tokens
            assert mock_db_session.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, token_repo, mock_db_session):
        """Test cleaning up expired tokens."""
        # Setup
        # Mock the select query result
        mock_select_result = Mock()
        mock_select_result.all.return_value = [(1, "hash1"), (2, "hash2")]

        # Mock the update operations (one per token)
        mock_update_results = [Mock() for _ in range(2)]

        # Configure mock to return different results based on call
        mock_db_session.execute.side_effect = [
            mock_select_result] + mock_update_results

        with patch.object(token_repo, '_remove_from_redis', new_callable=AsyncMock):
            # Test
            result = await token_repo.cleanup_expired_tokens()

            # Assert
            assert result == 2  # Should clean up 2 tokens
            assert mock_db_session.execute.call_count == 3  # 1 select + 2 updates
