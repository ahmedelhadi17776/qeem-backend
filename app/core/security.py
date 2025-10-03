"""Security helpers for JWT and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()


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
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.security.jwt_expires_in_days)
    )
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(
        to_encode,
        settings.security.jwt_secret,
        algorithm=settings.security.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(
            token,
            settings.security.jwt_secret,
            algorithms=[settings.security.jwt_algorithm],
        )
    except JWTError:
        return None
