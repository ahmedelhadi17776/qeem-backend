"""Audit log model for tracking user actions."""

from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, JSON
from sqlalchemy.sql import func

from .base import Base, IDMixin, TimestampMixin


class AuditLog(Base, IDMixin, TimestampMixin):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    # Nullable for anonymous actions
    user_id = Column(Integer, nullable=True, index=True)
    # e.g., "user_login", "rate_calculate"
    action = Column(String(100), nullable=False, index=True)
    # e.g., "user", "rate_calculation"
    resource_type = Column(String(50), nullable=True, index=True)
    # ID of the affected resource
    resource_id = Column(String(100), nullable=True, index=True)

    # Change tracking
    old_values = Column(JSON, nullable=True)  # Previous values (for updates)
    # New values (for creates/updates)
    new_values = Column(JSON, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)

    # Result tracking
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_message = Column(Text, nullable=True)

    # Additional metadata
    audit_metadata = Column(JSON, nullable=True)  # Additional context data

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
