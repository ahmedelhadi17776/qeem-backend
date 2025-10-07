# Qeem Backend - Production Features Documentation

## Overview

This document describes the production-ready features implemented in the Qeem backend to enhance security, monitoring, reliability, and maintainability.

## Table of Contents

1. [Database Transaction Management](#database-transaction-management)
2. [Email Verification System](#email-verification-system)
3. [Refresh Token System](#refresh-token-system)
4. [Security Headers Middleware](#security-headers-middleware)
5. [Enhanced Rate Limiting](#enhanced-rate-limiting)
6. [Prometheus Monitoring](#prometheus-monitoring)
7. [Comprehensive Audit Logging](#comprehensive-audit-logging)
8. [Enhanced Error Handling](#enhanced-error-handling)
9. [Database Connection Pooling](#database-connection-pooling)
10. [Configuration](#configuration)

## Database Transaction Management

### Overview

Implements proper transaction boundaries to ensure data consistency and atomicity of operations.

### Features

- **TransactionManager**: Async context manager for database transactions
- **Automatic Rollback**: Transactions are automatically rolled back on exceptions
- **Nested Transactions**: Support for savepoints in complex operations
- **Service Layer Control**: Services control transaction boundaries, repositories only execute queries

### Usage

```python
from app.db.database import get_transaction_manager

async with get_transaction_manager(db) as tx:
    # Multiple database operations
    user = await user_repo.create(user_data)
    profile = await user_repo.create_profile(profile_data)
    # Transaction commits automatically on success
    # Rolls back automatically on exception
```

### Benefits

- **Data Consistency**: Ensures all related operations succeed or fail together
- **Error Recovery**: Automatic rollback prevents partial updates
- **Performance**: Reduces database round trips

## Email Verification System

### Overview

Complete email verification system for user account validation.

### Features

- **SMTP Integration**: Configurable SMTP client with connection pooling
- **Token Generation**: Secure verification tokens with expiration
- **Email Templates**: HTML and plain text email templates
- **Resend Logic**: Ability to resend verification emails
- **Graceful Degradation**: System works even if SMTP is unavailable

### Configuration

```python
# Environment variables
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@qeem.com
SMTP_USE_TLS=true
VERIFICATION_TOKEN_TTL_HOURS=24
ENABLE_EMAIL_VERIFICATION=true
```

### API Endpoints

- `POST /auth/verify-email` - Verify email with token
- `POST /auth/resend-verification` - Resend verification email

### Usage

```python
from app.services.email_service import EmailService

email_service = EmailService(db)
await email_service.send_verification_email(user)
verified_user = await email_service.verify_email_token(token)
```

## Refresh Token System

### Overview

Secure refresh token system with token rotation for enhanced security.

### Features

- **Token Rotation**: New refresh token issued on each refresh
- **Token Families**: Track related tokens for security
- **Device Tracking**: Associate tokens with device information
- **Revocation**: Ability to revoke individual or all tokens
- **Expiration**: Configurable token expiration (default: 30 days)

### Security Features

- **Token Hashing**: Refresh tokens are hashed before storage
- **Family Revocation**: Compromised tokens revoke entire family
- **Device Binding**: Tokens can be associated with specific devices

### API Endpoints

- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout single device
- `POST /auth/logout-all` - Logout all devices

### Usage

```python
from app.services.user_service import UserService

user_service = UserService(db)
access_token, refresh_token = await user_service.refresh_access_token(old_refresh_token)
await user_service.logout_user(refresh_token)
await user_service.revoke_all_tokens(user_id)
```

## Security Headers Middleware

### Overview

Comprehensive security headers middleware to protect against common web vulnerabilities.

### Headers Implemented

- **X-Content-Type-Options**: Prevents MIME-sniffing attacks
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: Enables browser XSS filtering
- **Strict-Transport-Security**: Enforces HTTPS connections
- **Content-Security-Policy**: Prevents XSS and data injection attacks
- **Referrer-Policy**: Controls referrer information

### Environment-Specific Configuration

- **Production**: Strict CSP, HSTS enabled
- **Development**: Relaxed CSP for localhost, HSTS disabled

### Usage

```python
from app.middleware.security import get_security_headers_middleware

app.add_middleware(get_security_headers_middleware(environment="production"))
```

## Enhanced Rate Limiting

### Overview

Sophisticated rate limiting system with multiple strategies and endpoint-specific limits.

### Features

- **Sliding Window Algorithm**: More accurate than fixed windows
- **Per-User Limits**: Different limits for authenticated users
- **Endpoint-Specific**: Custom limits for different endpoints
- **IP Whitelisting**: Bypass rate limits for trusted IPs
- **Redis Backend**: Scalable across multiple instances

### Configuration

```python
# Environment variables
RATE_LIMITING_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_AUTH_LOGIN=5
RATE_LIMIT_AUTH_REGISTER=3
RATE_LIMIT_RATES_CALCULATE=20
RATE_LIMIT_MARKET=30
RATE_LIMIT_USER_MULTIPLIER=2.0
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,192.168.1.0/24
```

### Endpoint Limits

- **Login**: 5 requests/hour
- **Register**: 3 requests/hour
- **Rate Calculate**: 20 requests/hour
- **Market Data**: 30 requests/hour
- **Authenticated Users**: 2x multiplier

### Usage

```python
from app.api.rate_limit_deps import auth_login_rate_limit

@router.post("/login")
async def login(
    payload: UserLoginRequest,
    _: None = Depends(auth_login_rate_limit)
):
    # Endpoint protected by rate limiting
    pass
```

## Prometheus Monitoring

### Overview

Comprehensive monitoring system using Prometheus metrics for observability.

### Metrics Implemented

- **HTTP Metrics**: Request count, duration, status codes
- **Database Metrics**: Query count, duration, connection pool status
- **Cache Metrics**: Hit/miss rates, operation counts
- **Business Metrics**: User registrations, rate calculations, email sends
- **Custom Metrics**: Application-specific metrics

### Metrics Endpoint

- `GET /metrics` - Prometheus metrics endpoint

### Usage

```python
from app.infra.metrics import record_user_registration, record_rate_calculation

# Record business metrics
record_user_registration("email")
record_rate_calculation("web_development", "complex")
```

### Grafana Integration

Metrics can be visualized in Grafana dashboards for:

- Request rates and response times
- Database performance
- Cache efficiency
- Business metrics trends

## Comprehensive Audit Logging

### Overview

Complete audit logging system for tracking user actions and system events.

### Features

- **Action Tracking**: Log all significant user actions
- **Change Tracking**: Record old and new values for updates
- **Request Context**: Capture IP address, user agent, request ID
- **Async Logging**: Non-blocking audit log creation
- **Retention Policies**: Configurable log retention periods
- **Query Interface**: API endpoints for audit log retrieval

### Audit Events

- User registration and login
- Profile updates
- Rate calculations
- Email verification
- Token operations
- Administrative actions

### API Endpoints

- `GET /audit/logs/me` - User's own audit trail
- `GET /audit/logs` - All audit logs (admin only)
- `GET /audit/stats` - Audit statistics (admin only)
- `POST /audit/cleanup` - Clean old logs (admin only)

### Usage

```python
from app.services.audit_service import AuditService

audit_service = AuditService(db)
await audit_service.log_action(
    user_id=user.id,
    action="user_login",
    resource_type="user",
    resource_id=str(user.id),
    success=True
)
```

## Enhanced Error Handling

### Overview

Comprehensive error handling system with custom exceptions and user-friendly messages.

### Custom Exceptions

- **AuthenticationError**: Authentication failures
- **AuthorizationError**: Permission denied
- **ValidationError**: Input validation errors
- **NotFoundError**: Resource not found
- **RateLimitError**: Rate limit exceeded
- **EmailError**: Email operation failures
- **DatabaseError**: Database operation failures
- **TokenError**: Token operation failures

### Error Response Format

```json
{
  "error": {
    "message": "User-friendly error message",
    "code": "ERROR_CODE",
    "details": {
      "field": "additional context"
    },
    "request_id": "req-123"
  }
}
```

### Global Exception Handlers

- Custom exception handling
- HTTP exception handling
- Validation error handling
- Database error handling
- Generic exception handling

### Usage

```python
from app.core.exceptions import ValidationError, NotFoundError

# Raise custom exceptions
raise ValidationError("Invalid input", details={"field": "email"})
raise NotFoundError("User not found", details={"user_id": 123})
```

## Database Connection Pooling

### Overview

Explicit database connection pooling configuration for production environments.

### Features

- **Pool Size**: Configurable connection pool size
- **Max Overflow**: Additional connections beyond pool size
- **Connection Timeout**: Timeout for acquiring connections
- **Connection Recycle**: Automatic connection refresh
- **Pre-ping**: Validate connections before use
- **Health Monitoring**: Pool status in health checks

### Configuration

```python
# Environment variables
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_ECHO=false
```

### Health Check Integration

The `/health` endpoint includes database pool status:

```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "pool": {
        "pool_size": 20,
        "checked_in": 15,
        "checked_out": 5,
        "overflow": 0,
        "invalid": 0
      }
    }
  }
}
```

## Configuration

### Environment Variables

#### Database

```bash
DATABASE_URL=postgresql://user:pass@localhost/qeem
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_ECHO=false
```

#### Email

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@qeem.com
SMTP_USE_TLS=true
VERIFICATION_TOKEN_TTL_HOURS=24
ENABLE_EMAIL_VERIFICATION=true
```

#### Rate Limiting

```bash
RATE_LIMITING_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_AUTH_LOGIN=5
RATE_LIMIT_AUTH_REGISTER=3
RATE_LIMIT_RATES_CALCULATE=20
RATE_LIMIT_MARKET=30
RATE_LIMIT_USER_MULTIPLIER=2.0
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,192.168.1.0/24
```

#### Security

```bash
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN_DAYS=7
```

#### Redis

```bash
REDIS_URL=redis://localhost:6379/0
```

### Feature Flags

All features can be enabled/disabled via configuration:

- Email verification
- Rate limiting
- Audit logging
- Security headers
- Prometheus metrics

## Deployment Considerations

### Production Checklist

- [ ] Configure SMTP settings for email verification
- [ ] Set up Redis for rate limiting and caching
- [ ] Configure database connection pooling
- [ ] Set up Prometheus monitoring
- [ ] Configure security headers for production
- [ ] Set up log aggregation for audit logs
- [ ] Configure backup strategy for audit logs
- [ ] Set up alerting for critical metrics

### Security Considerations

- Use strong JWT secret keys
- Enable HTTPS in production
- Configure CSP policies carefully
- Monitor rate limiting effectiveness
- Regular security audits
- Keep dependencies updated

### Performance Considerations

- Monitor database connection pool usage
- Optimize audit log queries
- Configure appropriate cache TTLs
- Monitor rate limiting impact
- Set up performance alerts

## Monitoring and Alerting

### Key Metrics to Monitor

- Request rate and response times
- Database connection pool usage
- Cache hit/miss rates
- Rate limiting effectiveness
- Email delivery success rates
- Audit log volume

### Recommended Alerts

- High error rates (>5%)
- Database connection pool exhaustion
- Rate limiting triggered frequently
- Email delivery failures
- Unusual audit log patterns

## Troubleshooting

### Common Issues

1. **Email verification not working**: Check SMTP configuration
2. **Rate limiting too strict**: Adjust limits in configuration
3. **Database connection issues**: Check pool configuration
4. **Audit logs not appearing**: Verify async logging is working
5. **Security headers blocking requests**: Adjust CSP policy

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Conclusion

The Qeem backend now includes comprehensive production-ready features for security, monitoring, reliability, and maintainability. These features work together to provide a robust, scalable, and secure platform for freelance rate calculations.

For additional support or questions, please refer to the API documentation or contact the development team.
