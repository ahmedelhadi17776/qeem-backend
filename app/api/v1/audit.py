"""Audit API endpoints for querying audit logs."""

from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...schemas.audit import (
    AuditTrailResponse,
    AuditStatsResponse,
)
from ...services.audit_service import AuditService
from ..deps import get_db, get_current_active_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs/me", response_model=AuditTrailResponse)
async def get_my_audit_trail(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    action: Optional[str] = Query(None, description="Filter by action"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of logs to return"
    ),
) -> AuditTrailResponse:
    """Get audit trail for the current user."""
    audit_service = AuditService(db)

    logs = await audit_service.get_user_audit_trail(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )

    return AuditTrailResponse(
        items=logs,
        # This is simplified - in production you'd get actual total
        total=len(logs),
        skip=skip,
        limit=limit,
    )


@router.get("/logs", response_model=AuditTrailResponse)
async def get_audit_logs(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of logs to return"
    ),
) -> AuditTrailResponse:
    """Get audit logs (admin only)."""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    audit_service = AuditService(db)

    # This is a simplified implementation
    # In production, you'd implement proper filtering in the repository
    logs = await audit_service.get_action_audit_trail(
        action=action or "all",
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )

    return AuditTrailResponse(
        items=logs,
        # This is simplified - in production you'd get actual total
        total=len(logs),
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
) -> AuditStatsResponse:
    """Get audit statistics (admin only)."""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    audit_service = AuditService(db)
    stats = await audit_service.get_audit_stats(start_date, end_date)

    return AuditStatsResponse(**stats)


@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_logs(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    retention_days: int = Query(
        90, ge=1, le=365, description="Retention period in days"
    ),
) -> dict:
    """Clean up old audit logs (admin only)."""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    audit_service = AuditService(db)
    count = await audit_service.cleanup_old_logs(retention_days)

    return {"message": f"Cleaned up {count} old audit logs"}
