"""Audit service for managing audit logging operations."""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from queue import Queue
from threading import Thread

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.audit_repository import AuditRepository
from ..core.config import get_settings
from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)
settings = get_settings()


class AuditService:
    """Service for audit logging operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self._log_queue: Queue = Queue()
        self._worker_thread = None
        self._shutdown_event = asyncio.Event()

    def start_background_worker(self):
        """Start background worker for async audit logging."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._worker_thread = Thread(target=self._background_worker, daemon=True)
        self._worker_thread.start()
        logger.info("Audit service background worker started")

    def stop_background_worker(self):
        """Stop background worker."""
        if self._worker_thread and self._worker_thread.is_alive():
            self._log_queue.put(None)  # Signal shutdown
            self._worker_thread.join(timeout=5)
            logger.info("Audit service background worker stopped")

    def _background_worker(self):
        """Background worker for processing audit logs."""
        while True:
            try:
                log_data = self._log_queue.get(timeout=1)
                if log_data is None:  # Shutdown signal
                    break

                # Process log data
                asyncio.run(self._process_log_data(log_data))
                self._log_queue.task_done()

            except Exception as e:
                logger.error(f"Error in audit background worker: {e}")

    async def _process_log_data(self, log_data: Dict[str, Any]):
        """Process audit log data."""
        try:
            await self.audit_repo.create_audit_log(**log_data)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    def log_action_async(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log action asynchronously (non-blocking)."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
            "success": success,
            "error_message": error_message,
            "audit_metadata": audit_metadata,
        }

        try:
            self._log_queue.put_nowait(log_data)
        except Exception as e:
            logger.error(f"Failed to queue audit log: {e}")

    async def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log action synchronously."""
        return await self.audit_repo.create_audit_log(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
            audit_metadata=audit_metadata,
        )

    async def get_user_audit_trail(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a user."""
        logs = await self.audit_repo.get_audit_logs_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            action=action,
            start_date=start_date,
            end_date=end_date,
        )

        return [self._serialize_audit_log(log) for log in logs]

    async def get_action_audit_trail(
        self,
        action: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific action."""
        logs = await self.audit_repo.get_audit_logs_by_action(
            action=action,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        return [self._serialize_audit_log(log) for log in logs]

    async def get_resource_audit_trail(
        self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific resource."""
        logs = await self.audit_repo.get_audit_logs_by_resource(
            resource_type=resource_type, resource_id=resource_id, skip=skip, limit=limit
        )

        return [self._serialize_audit_log(log) for log in logs]

    async def get_audit_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics."""
        return await self.audit_repo.get_audit_stats(start_date, end_date)

    async def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """Clean up old audit logs."""
        return await self.audit_repo.cleanup_old_logs(retention_days)

    def _serialize_audit_log(self, log) -> Dict[str, Any]:
        """Serialize audit log for API response."""
        return {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_id": log.request_id,
            "success": log.success,
            "error_message": log.error_message,
            "audit_metadata": log.audit_metadata,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
