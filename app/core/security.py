"""Security helpers for JWT and password hashing."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from secrets import token_urlsafe

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from .config import get_settings


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    settings = get_settings()
    if expires_delta is not None:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.security.jwt_expires_in_days
        )
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)

    jwt_secret = settings.security.jwt_secret
    if jwt_secret is None:
        raise ValueError("JWT secret is not configured")

    return jwt.encode(
        to_encode,
        jwt_secret,
        algorithm=settings.security.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        settings = get_settings()
        jwt_secret = settings.security.jwt_secret
        if jwt_secret is None:
            return None

        return jwt.decode(
            token,
            jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
        )
    except InvalidTokenError:
        return None


def create_refresh_token() -> str:
    """Generate a secure refresh token."""
    return token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token(token: str, hashed_token: str) -> bool:
    """Verify refresh token against its hash."""
    return hash_refresh_token(token) == hashed_token


def create_token_family() -> str:
    """Create a token family identifier for token rotation."""
    return token_urlsafe(16)
