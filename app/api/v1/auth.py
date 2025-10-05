from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...models.user import User
from ...schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from ...services.user_service import UserService
from ..deps import get_db, get_current_active_user

# OAuth2 standard token type
TOKEN_TYPE = "Bearer"  # nosec

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: UserRegisterRequest, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user account.

    Creates a new user with email/password authentication and basic profile.
    """
    try:
        user_service = UserService(db)
        user = user_service.create_user(payload)

        # Return user without sensitive data
        return UserResponse.model_validate(user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user_service = UserService(db)
    user = user_service.authenticate_user(payload.email, payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = user_service.create_access_token_for_user(user)

    # Calculate expiration time
    expires_in = (
        settings.security.jwt_expires_in_days * 24 * 60 * 60
    )  # Convert days to seconds

    return TokenResponse(
        access_token=access_token, token_type=TOKEN_TYPE, expires_in=expires_in
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserResponse:
    """Get current authenticated user information."""
    # current_user is now a User object from the dependency
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str, db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh JWT token.

    Note: This is a simplified implementation. In production, you'd want to:
    1. Implement refresh token rotation
    2. Store refresh tokens in Redis/database
    3. Add token blacklisting
    """
    # For now, just return a new token based on the current user
    # In a real implementation, you'd validate the refresh token first
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not yet implemented",
    )
