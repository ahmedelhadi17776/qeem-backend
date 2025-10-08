import pytest
from app.core.exceptions import (
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
    AuditError
)


class TestAdditionalCoverage:
    """Additional tests for coverage increase."""

    def test_qeem_exception_base(self):
        """Test base QeemException."""
        exc = QeemException("Test message", "TEST_CODE", {"detail": "test"})
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"detail": "test"}
        assert str(exc) == "Test message"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Auth failed")
        assert exc.message == "Auth failed"
        assert exc.error_code == "AUTH_ERROR"

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError("Not authorized")
        assert exc.message == "Not authorized"
        assert exc.error_code == "AUTHZ_ERROR"

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid data")
        assert exc.message == "Invalid data"
        assert exc.error_code == "VALIDATION_ERROR"

    def test_not_found_error(self):
        """Test NotFoundError."""
        exc = NotFoundError("Not found")
        assert exc.message == "Not found"
        assert exc.error_code == "NOT_FOUND"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError("Too many requests")
        assert exc.message == "Too many requests"
        assert exc.error_code == "RATE_LIMIT_ERROR"

    def test_email_error(self):
        """Test EmailError."""
        exc = EmailError("Email failed")
        assert exc.message == "Email failed"
        assert exc.error_code == "EMAIL_ERROR"

    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("DB failed")
        assert exc.message == "DB failed"
        assert exc.error_code == "DATABASE_ERROR"

    def test_external_service_error(self):
        """Test ExternalServiceError."""
        exc = ExternalServiceError("Service failed")
        assert exc.message == "Service failed"
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("Config failed")
        assert exc.message == "Config failed"
        assert exc.error_code == "CONFIG_ERROR"

    def test_token_error(self):
        """Test TokenError."""
        exc = TokenError("Token failed")
        assert exc.message == "Token failed"
        assert exc.error_code == "TOKEN_ERROR"

    def test_audit_error(self):
        """Test AuditError."""
        exc = AuditError("Audit failed")
        assert exc.message == "Audit failed"
        assert exc.error_code == "AUDIT_ERROR"
