"""FastAPI dependencies for database sessions and authentication."""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..core.security import decode_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User data from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: In a real implementation, you would:
    # 1. Extract user_id from payload
    # 2. Query database to get full user object
    # 3. Return user object instead of payload

    return payload


def get_current_active_user(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """Get current active user (non-disabled).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user data

    Raises:
        HTTPException: If user is disabled
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # TODO: Check if user is active/not disabled
    # if not current_user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Inactive user"
    #     )

    return current_user
