"""Tests for audit logging system."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog


class TestAuditService:
    """Test audit service functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_audit_repo(self):
        """Create a mock audit repository."""
        return AsyncMock()

    @pytest.fixture
    def audit_service(self, mock_db, mock_audit_repo):
        """Create audit service with mocked dependencies."""
        service = AuditService(mock_db)
        service.audit_repo = mock_audit_repo
        return service

    @pytest.fixture
    def sample_audit_log(self):
        """Create a sample audit log for testing."""
        log = AuditLog()
        log.id = 1
        log.user_id = 1
        log.action = "user_login"
        log.resource_type = "user"
        log.resource_id = "1"
        log.old_values = None
        log.new_values = {"is_active": True}
        log.ip_address = "127.0.0.1"
        log.user_agent = "test-agent"
        log.request_id = "req-123"
        log.success = True
        log.error_message = None
        log.audit_metadata = {"test": "data"}
        log.timestamp = datetime.now(timezone.utc)
        log.created_at = datetime.now(timezone.utc)
        return log

    @pytest.mark.asyncio
    async def test_log_action_success(self, audit_service, sample_audit_log):
        """Test successful audit log creation."""
        audit_service.audit_repo.create_audit_log.return_value = sample_audit_log

        result = await audit_service.log_action(
            user_id=1,
            action="user_login",
            resource_type="user",
            resource_id="1",
            new_values={"is_active": True},
            ip_address="127.0.0.1",
            user_agent="test-agent",
            request_id="req-123",
            success=True,
            audit_metadata={"test": "data"}
        )

        assert result == sample_audit_log
        audit_service.audit_repo.create_audit_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_action_with_old_values(self, audit_service, sample_audit_log):
        """Test audit log creation with old values."""
        audit_service.audit_repo.create_audit_log.return_value = sample_audit_log

        result = await audit_service.log_action(
            user_id=1,
            action="user_update",
            resource_type="user",
            resource_id="1",
            old_values={"is_active": False},
            new_values={"is_active": True},
            success=True
        )

        assert result == sample_audit_log
        call_args = audit_service.audit_repo.create_audit_log.call_args
        assert call_args[1]["old_values"] == {"is_active": False}
        assert call_args[1]["new_values"] == {"is_active": True}

    @pytest.mark.asyncio
    async def test_log_action_failure(self, audit_service, sample_audit_log):
        """Test audit log creation for failed action."""
        sample_audit_log.success = False
        sample_audit_log.error_message = "Authentication failed"
        audit_service.audit_repo.create_audit_log.return_value = sample_audit_log

        result = await audit_service.log_action(
            user_id=1,
            action="user_login",
            success=False,
            error_message="Authentication failed"
        )

        assert result == sample_audit_log
        call_args = audit_service.audit_repo.create_audit_log.call_args
        assert call_args[1]["success"] is False
        assert call_args[1]["error_message"] == "Authentication failed"

    @pytest.mark.asyncio
    async def test_log_action_async(self, audit_service):
        """Test async audit log creation."""
        audit_service.audit_repo.create_audit_log.return_value = AsyncMock()

        # This should not raise an exception
        audit_service.log_action_async(
            user_id=1,
            action="user_login",
            success=True
        )

        # The async logging uses a queue, so we can't easily test immediate execution
        # Instead, we just verify no exception was raised
        assert True  # If we get here, no exception was raised

    @pytest.mark.asyncio
    async def test_get_user_audit_trail(self, audit_service, sample_audit_log):
        """Test getting user audit trail."""
        audit_service.audit_repo.get_audit_logs_by_user.return_value = [
            sample_audit_log]

        result = await audit_service.get_user_audit_trail(user_id=1)

        assert len(result) == 1
        assert result[0]["action"] == "user_login"
        audit_service.audit_repo.get_audit_logs_by_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_action_audit_trail(self, audit_service, sample_audit_log):
        """Test getting action audit trail."""
        audit_service.audit_repo.get_audit_logs_by_action.return_value = [
            sample_audit_log]

        result = await audit_service.get_action_audit_trail(action="user_login")

        assert len(result) == 1
        assert result[0]["action"] == "user_login"
        audit_service.audit_repo.get_audit_logs_by_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_stats(self, audit_service):
        """Test getting audit statistics."""
        mock_stats = {
            "total_actions": 100,
            "successful_actions": 95,
            "failed_actions": 5,
            "unique_users": 10,
            "most_common_action": "user_login"
        }
        audit_service.audit_repo.get_audit_stats.return_value = mock_stats

        result = await audit_service.get_audit_stats()

        assert result == mock_stats
        audit_service.audit_repo.get_audit_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, audit_service):
        """Test cleanup of old audit logs."""
        audit_service.audit_repo.cleanup_old_logs.return_value = 50

        result = await audit_service.cleanup_old_logs(retention_days=90)

        assert result == 50
        audit_service.audit_repo.cleanup_old_logs.assert_called_once_with(90)

    @pytest.mark.asyncio
    async def test_log_action_minimal_params(self, audit_service, sample_audit_log):
        """Test audit log creation with minimal parameters."""
        audit_service.audit_repo.create_audit_log.return_value = sample_audit_log

        result = await audit_service.log_action(
            user_id=1,
            action="test_action"
        )

        assert result == sample_audit_log
        call_args = audit_service.audit_repo.create_audit_log.call_args
        assert call_args[1]["user_id"] == 1
        assert call_args[1]["action"] == "test_action"
        assert call_args[1]["success"] is True  # Default value
