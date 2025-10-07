"""Audit schemas for API responses."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    id: int = Field(..., description="Audit log ID")
    user_id: Optional[int] = Field(None, description="User ID")
    action: str = Field(..., description="Action performed")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    request_id: Optional[str] = Field(None, description="Request ID")
    success: bool = Field(..., description="Whether action was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    audit_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )
    timestamp: str = Field(..., description="Action timestamp")
    created_at: str = Field(..., description="Log creation timestamp")


class AuditTrailResponse(BaseModel):
    """Audit trail response schema."""

    items: List[AuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of logs")
    skip: int = Field(..., description="Number of logs skipped")
    limit: int = Field(..., description="Maximum number of logs returned")


class AuditStatsResponse(BaseModel):
    """Audit statistics response schema."""

    total_logs: int = Field(..., description="Total number of audit logs")
    failed_logs: int = Field(..., description="Number of failed actions")
    success_rate: float = Field(..., description="Success rate (0-1)")
    top_actions: Dict[str, int] = Field(..., description="Top actions by count")


class AuditQueryRequest(BaseModel):
    """Audit query request schema."""

    action: Optional[str] = Field(None, description="Filter by action")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    success: Optional[bool] = Field(None, description="Filter by success status")
    skip: int = Field(default=0, ge=0, description="Number of logs to skip")
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of logs to return"
    )
