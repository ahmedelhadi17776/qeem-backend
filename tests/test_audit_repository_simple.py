"""Simple tests for audit repository."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from app.repositories.audit_repository import AuditRepository


class TestAuditRepository:
    """Test AuditRepository basic functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def audit_repo(self, mock_db_session):
        """Create AuditRepository instance."""
        return AuditRepository(mock_db_session)

    @pytest.mark.asyncio
    async def test_create_audit_log(self, audit_repo, mock_db_session):
        """Test creating an audit log."""
        # Setup
        user_id = 1
        action = "test_action"
        resource_type = "user"
        resource_id = "123"

        # Mock the audit log creation
        mock_audit_log = Mock()
        mock_audit_log.id = 1
        mock_audit_log.user_id = user_id
        mock_audit_log.action = action
        mock_audit_log.resource_type = resource_type
        mock_audit_log.resource_id = resource_id

        with patch('app.repositories.audit_repository.AuditLog', return_value=mock_audit_log):
            # Test
            result = await audit_repo.create_audit_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id
            )

            # Assert
            assert result == mock_audit_log
            mock_db_session.add.assert_called_once()
            mock_db_session.flush.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_logs_by_user(self, audit_repo, mock_db_session):
        """Test getting audit logs by user."""
        # Setup
        user_id = 1
        mock_logs = [Mock(), Mock()]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await audit_repo.get_audit_logs_by_user(user_id)

        # Assert
        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_logs_by_action(self, audit_repo, mock_db_session):
        """Test getting audit logs by action."""
        # Setup
        action = "login"
        mock_logs = [Mock()]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await audit_repo.get_audit_logs_by_action(action)

        # Assert
        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_logs_by_resource(self, audit_repo, mock_db_session):
        """Test getting audit logs by resource."""
        # Setup
        resource_type = "user"
        resource_id = "123"
        mock_logs = [Mock()]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await audit_repo.get_audit_logs_by_resource(resource_type, resource_id)

        # Assert
        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_failed_audit_logs(self, audit_repo, mock_db_session):
        """Test getting failed audit logs."""
        # Setup
        mock_logs = [Mock()]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_db_session.execute.return_value = mock_result

        # Test
        result = await audit_repo.get_failed_audit_logs()

        # Assert
        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_stats(self, audit_repo, mock_db_session):
        """Test getting audit statistics."""
        # Setup - Mock multiple execute calls for different queries
        mock_stats = {"total": 100, "successful": 95, "failed": 5}

        # Mock the scalar results for total and failed counts
        mock_scalar_result = Mock()
        mock_scalar_result.scalar.return_value = 100

        # Mock the fetchall result for actions
        mock_fetchall_result = Mock()
        mock_fetchall_result.fetchall.return_value = [
            ("login", 50), ("logout", 30)]

        # Configure mock to return different results based on call
        mock_db_session.execute.side_effect = [
            mock_scalar_result,  # Total count query
            mock_scalar_result,  # Failed count query
            mock_fetchall_result  # Actions query
        ]

        # Test
        result = await audit_repo.get_audit_stats()

        # Assert
        assert "total_logs" in result
        assert "failed_logs" in result
        assert "top_actions" in result
        assert mock_db_session.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, audit_repo, mock_db_session):
        """Test cleaning up old audit logs."""
        # Setup
        retention_days = 90
        deleted_count = 5

        # Mock the select query result
        mock_select_result = Mock()
        mock_select_result.scalars.return_value.all.return_value = [
            Mock() for _ in range(deleted_count)]

        # Mock the delete operations (one per log) - these are direct delete calls, not execute calls
        mock_db_session.delete = AsyncMock()

        # Configure mock to return different results based on call
        mock_db_session.execute.return_value = mock_select_result

        # Test
        result = await audit_repo.cleanup_old_logs(retention_days)

        # Assert
        assert result == deleted_count
        assert mock_db_session.execute.call_count == 1  # Only the select call
        assert mock_db_session.delete.call_count == deleted_count  # One delete per log
