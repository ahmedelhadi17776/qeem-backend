"""Audit middleware for capturing request details."""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request details for audit logging."""

    def __init__(self, app, audit_service=None):
        super().__init__(app)
        self.audit_service = audit_service

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Capture request details and add to request state."""

        # Extract request details
        request_details = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": getattr(request.state, "request_id", None),
        }

        # Add to request state for use in endpoints
        request.state.audit_details = request_details

        # Process request
        response = await call_next(request)

        # Add response details
        request_details["status_code"] = response.status_code
        request.state.audit_details = request_details

        return response


def get_audit_details(request: Request) -> dict:
    """Get audit details from request state."""
    return getattr(request.state, "audit_details", {})
