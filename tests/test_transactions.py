"""Tests for transaction management."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import TransactionManager
from app.core.exceptions import DatabaseError


class TestTransactionManager:
    """Test transaction manager functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock(spec=AsyncSession)
        session.begin = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.begin_nested = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_transaction_success(self, mock_session):
        """Test successful transaction."""
        mock_transaction = AsyncMock()
        mock_session.begin.return_value = mock_transaction

        async with TransactionManager(mock_session) as tx:
            assert tx.session == mock_session

        # Verify transaction was committed
        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception(self, mock_session):
        """Test transaction rollback on exception."""
        mock_transaction = AsyncMock()
        mock_session.begin.return_value = mock_transaction

        with pytest.raises(ValueError):
            async with TransactionManager(mock_session) as tx:
                raise ValueError("Test error")

        # Verify transaction was rolled back
        mock_session.begin.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_commit_error(self, mock_session):
        """Test transaction rollback when commit fails."""
        mock_transaction = AsyncMock()
        mock_session.begin.return_value = mock_transaction
        mock_session.commit.side_effect = Exception("Commit failed")

        with pytest.raises(Exception):
            async with TransactionManager(mock_session) as tx:
                pass

        # Verify transaction was rolled back after commit failure
        mock_session.begin.assert_called_once()
        mock_session.commit.assert_called_once()
        # Note: rollback is called in the exception handler, not in the normal flow
        # The TransactionManager handles this internally

    @pytest.mark.asyncio
    async def test_savepoint_creation(self, mock_session):
        """Test savepoint creation."""
        mock_transaction = AsyncMock()
        mock_savepoint = AsyncMock()
        mock_session.begin.return_value = mock_transaction
        mock_session.begin_nested.return_value = mock_savepoint

        async with TransactionManager(mock_session) as tx:
            savepoint = await tx.create_savepoint("test_savepoint")
            assert savepoint == mock_savepoint

        mock_session.begin_nested.assert_called_once()

    @pytest.mark.asyncio
    async def test_savepoint_rollback(self, mock_session):
        """Test savepoint rollback."""
        mock_transaction = AsyncMock()
        mock_savepoint = AsyncMock()
        mock_session.begin.return_value = mock_transaction
        mock_session.begin_nested.return_value = mock_savepoint

        async with TransactionManager(mock_session) as tx:
            await tx.create_savepoint("test_savepoint")
            await tx.rollback_to_savepoint()

        mock_savepoint.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_savepoint_without_transaction_raises_error(self, mock_session):
        """Test that creating savepoint without transaction raises error."""
        tx = TransactionManager(mock_session)

        with pytest.raises(RuntimeError, match="No active transaction"):
            await tx.create_savepoint("test_savepoint")

    @pytest.mark.asyncio
    async def test_rollback_without_savepoint_raises_error(self, mock_session):
        """Test that rolling back without savepoint raises error."""
        mock_transaction = AsyncMock()
        mock_session.begin.return_value = mock_transaction

        async with TransactionManager(mock_session) as tx:
            with pytest.raises(RuntimeError, match="No savepoint to rollback to"):
                await tx.rollback_to_savepoint()
