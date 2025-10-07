from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...models.user import User
from ...schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    EmailVerificationRequest,
    ResendVerificationRequest,
)
from ...services.user_service import UserService
from ...services.email_service import EmailService
from ..deps import get_db, get_current_active_user

# OAuth2 standard token type
TOKEN_TYPE = "Bearer"  # nosec

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Register a new user account.

    Creates a new user with email/password authentication and basic profile.
    """
    try:
        user_service = UserService(db)
        user = await user_service.create_user(payload)

        # Convert user to dict before detaching from session
        user_dict = {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }
        return UserResponse.model_validate(user_dict)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """Verify user email with token."""
    email_service = EmailService(db)
    user = await email_service.verify_email_token(payload.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    return {"message": "Email verified successfully", "user_id": user.id}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification_email(
    payload: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    """Resend verification email to user."""
    user_service = UserService(db)
    email_service = EmailService(db)
    
    user = await user_service.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    success = await email_service.resend_verification_email(user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "Verification email sent successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user_service = UserService(db)
    user = await user_service.authenticate_user(payload.email, payload.password)

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
    # Convert user to dict (user is already detached by dependency)
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }
    return UserResponse.model_validate(user_dict)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str, db: AsyncSession = Depends(get_db)
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
