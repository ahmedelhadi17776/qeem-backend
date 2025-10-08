"""Custom exception classes for the Qeem backend."""

from typing import Optional, Dict, Any


class QeemException(Exception):
    """Base exception class for Qeem application."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(QeemException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(QeemException):
    """Raised when user lacks permission for an action."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUTHZ_ERROR", details)


class ValidationError(QeemException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(QeemException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "NOT_FOUND", details)


class RateLimitError(QeemException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class EmailError(QeemException):
    """Raised when email operations fail."""

    def __init__(
        self,
        message: str = "Email operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "EMAIL_ERROR", details)


class DatabaseError(QeemException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "DATABASE_ERROR", details)


class ExternalServiceError(QeemException):
    """Raised when external service calls fail."""

    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class ConfigurationError(QeemException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "CONFIG_ERROR", details)


class TokenError(QeemException):
    """Raised when token operations fail."""

    def __init__(
        self,
        message: str = "Token operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "TOKEN_ERROR", details)


class AuditError(QeemException):
    """Raised when audit logging fails."""

    def __init__(
        self,
        message: str = "Audit logging failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, "AUDIT_ERROR", details)
