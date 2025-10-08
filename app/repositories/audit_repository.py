"""Audit repository for managing audit logs."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_audit_log(
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
        """Create a new audit log entry."""
        audit_log = AuditLog(
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

        self.db.add(audit_log)
        await self.db.flush()
        await self.db.refresh(audit_log)

        return audit_log

    async def get_audit_logs_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        stmt = select(AuditLog).where(AuditLog.user_id == user_id)

        if action:
            stmt = stmt.where(AuditLog.action == action)

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        stmt = stmt.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_audit_logs_by_action(
        self,
        action: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """Get audit logs for a specific action."""
        stmt = select(AuditLog).where(AuditLog.action == action)

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        stmt = stmt.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_audit_logs_by_resource(
        self, resource_type: str, resource_id: str, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific resource."""
        stmt = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id,
                )
            )
            .order_by(desc(AuditLog.timestamp))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """Get failed audit logs."""
        stmt = select(AuditLog).where(AuditLog.success.is_not(True))

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        stmt = stmt.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_audit_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics."""
        base_query = select(AuditLog)

        if start_date:
            base_query = base_query.where(AuditLog.timestamp >= start_date)

        if end_date:
            base_query = base_query.where(AuditLog.timestamp <= end_date)

        # Total logs
        total_result = await self.db.execute(
            select(func.count(AuditLog.id)).select_from(base_query.subquery())
        )
        total_logs = total_result.scalar() or 0

        # Failed logs
        failed_result = await self.db.execute(
            select(func.count(AuditLog.id)).select_from(
                base_query.where(AuditLog.success.is_not(True)).subquery()
            )
        )
        failed_logs = failed_result.scalar() or 0

        # Actions count
        actions_result = await self.db.execute(
            select(AuditLog.action, func.count(AuditLog.id))
            .select_from(base_query.subquery())
            .group_by(AuditLog.action)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(10)
        )
        top_actions: Dict[str, int] = {
            row[0]: row[1] for row in actions_result.fetchall()
        }

        return {
            "total_logs": total_logs,
            "failed_logs": failed_logs,
            "success_rate": (
                (total_logs - failed_logs) / total_logs if total_logs > 0 else 0
            ),
            "top_actions": top_actions,
        }

    async def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """Clean up old audit logs based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        stmt = select(AuditLog).where(AuditLog.timestamp < cutoff_date)
        result = await self.db.execute(stmt)
        old_logs = result.scalars().all()

        count = 0
        for log in old_logs:
            await self.db.delete(log)
            count += 1

        await self.db.flush()
        logger.info(f"Cleaned up {count} old audit logs")
        return count
