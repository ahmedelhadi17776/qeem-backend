"""Global exception handlers for the Qeem backend."""

import logging

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .exceptions import (
    QeemException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    EmailError,
    DatabaseError,
    ExternalServiceError,
    ConfigurationError,
    TokenError,
    AuditError,
)
from typing import Optional

logger = logging.getLogger(__name__)


def create_error_response(
    message: str,
    error_code: str,
    status_code: int,
    details: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Create standardized error response."""
    error_response = {
        "error": {"message": message, "code": error_code, "details": details or {}}
    }

    if request_id:
        error_response["error"]["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=error_response)


async def qeem_exception_handler(request: Request, exc: QeemException) -> JSONResponse:
    """Handle custom Qeem exceptions."""
    request_id = getattr(request.state, "request_id", None)

    # Map exception types to HTTP status codes
    status_code_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        EmailError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        TokenError: status.HTTP_401_UNAUTHORIZED,
        AuditError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Log the exception
    logger.error(
        f"Qeem exception: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        message=exc.message,
        error_code=exc.error_code or "UNKNOWN_ERROR",
        status_code=status_code,
        details=exc.details,
        request_id=request_id,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # For tests, return simple format with detail field
    if request.url.path.startswith("/api/v1/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # For other endpoints, use custom error format
    return create_error_response(
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        status_code=exc.status_code,
        request_id=request_id or "unknown",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", None)

    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

    logger.warning(
        f"Validation error: {len(errors)} field(s) invalid",
        extra={
            "request_id": request_id,
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        message="Invalid input - please check your data",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        request_id=request_id or "unknown",
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    request_id = getattr(request.state, "request_id", None)

    # Map specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        message = "Database integrity error - resource may already exist"
        error_code = "DATABASE_INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
    else:
        message = "Database operation failed - please try again"
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        f"Database error: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return create_error_response(
        message=message,
        error_code=error_code,
        status_code=status_code,
        request_id=request_id or "unknown",
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        f"Unexpected error: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    return create_error_response(
        message="An unexpected error occurred - please try again",
        error_code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id or "unknown",
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""

    # Custom Qeem exceptions
    app.add_exception_handler(QeemException, qeem_exception_handler)
    app.add_exception_handler(AuthenticationError, qeem_exception_handler)
    app.add_exception_handler(AuthorizationError, qeem_exception_handler)
    app.add_exception_handler(ValidationError, qeem_exception_handler)
    app.add_exception_handler(NotFoundError, qeem_exception_handler)
    app.add_exception_handler(RateLimitError, qeem_exception_handler)
    app.add_exception_handler(EmailError, qeem_exception_handler)
    app.add_exception_handler(DatabaseError, qeem_exception_handler)
    app.add_exception_handler(ExternalServiceError, qeem_exception_handler)
    app.add_exception_handler(ConfigurationError, qeem_exception_handler)
    app.add_exception_handler(TokenError, qeem_exception_handler)
    app.add_exception_handler(AuditError, qeem_exception_handler)

    # Standard exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Generic exception handler (must be last)
    app.add_exception_handler(Exception, generic_exception_handler)
