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
    RefreshTokenRequest,
    LogoutRequest,
)
from ...api.rate_limit_deps import auth_login_rate_limit, auth_register_rate_limit
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
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(auth_register_rate_limit),
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
            detail="Invalid or expired verification token",
        )

    return {"message": "Email verified successfully", "user_id": int(user.id)}


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
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified"
        )

    success = await email_service.resend_verification_email(user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )

    return {"message": "Verification email sent successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(auth_login_rate_limit),
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

    # Create token pair
    access_token, refresh_token, token_hash, token_family, expires_at = (
        user_service.create_token_pair(user)
    )

    # Store refresh token
    await user_service.token_repo.create_refresh_token(
        user_id=int(user.id),
        token_hash=token_hash,
        expires_at=expires_at,
        token_family=token_family,
    )

    # Calculate expiration time
    expires_in = (
        settings.security.jwt_expires_in_days * 24 * 60 * 60
    )  # Convert days to seconds

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=TOKEN_TYPE,
        expires_in=expires_in,
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
    payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Refresh JWT token using refresh token."""
    user_service = UserService(db)
    result = await user_service.refresh_access_token(payload.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token = result

    # Calculate expiration time
    expires_in = (
        settings.security.jwt_expires_in_days * 24 * 60 * 60
    )  # Convert days to seconds

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=TOKEN_TYPE,
        expires_in=expires_in,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Logout user by revoking refresh token."""
    user_service = UserService(db)
    success = await user_service.logout_user(payload.refresh_token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token"
        )

    return {"message": "Logged out successfully"}


@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all_devices(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout user from all devices by revoking all refresh tokens."""
    user_service = UserService(db)
    count = await user_service.revoke_all_tokens(int(current_user.id))

    return {"message": f"Logged out from {count} devices"}
