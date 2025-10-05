"""User profile management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.auth import (
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from ...services.user_service import UserService
from ..deps import get_db, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Get current user's profile information."""
    user_service = UserService(db)

    # Get user with profile
    user_with_profile = user_service.get_user_with_profile(int(current_user.id))

    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    user, profile = user_with_profile

    # Combine user and profile data
    profile_data = {
        "id": user.id,
        "email": user.email,
        "first_name": profile.first_name if profile else None,
        "last_name": profile.last_name if profile else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "phone": profile.phone if profile else None,
        "bio": profile.bio if profile else None,
        "profession": profile.profession if profile else None,
        "experience_years": profile.experience_years if profile else None,
        "skills": profile.skills if profile else None,
        "portfolio_url": profile.portfolio_url if profile else None,
        "linkedin_url": profile.linkedin_url if profile else None,
        "city": profile.city if profile else None,
        "country": profile.country if profile else None,
        "preferred_currency": profile.preferred_currency if profile else None,
        "hourly_rate_preference": profile.hourly_rate_preference if profile else None,
    }

    return UserProfileResponse.model_validate(profile_data)


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Update current user's profile information."""
    user_service = UserService(db)

    # Update profile
    updated_profile = user_service.update_user_profile(
        int(current_user.id), profile_data
    )

    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    # Get updated user with profile
    user_with_profile = user_service.get_user_with_profile(int(current_user.id))

    if not user_with_profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated profile",
        )

    user, profile = user_with_profile

    # Combine user and profile data
    response_data = {
        "id": user.id,
        "email": user.email,
        "first_name": profile.first_name if profile else None,
        "last_name": profile.last_name if profile else None,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "phone": profile.phone if profile else None,
        "bio": profile.bio if profile else None,
        "profession": profile.profession if profile else None,
        "experience_years": profile.experience_years if profile else None,
        "skills": profile.skills if profile else None,
        "portfolio_url": profile.portfolio_url if profile else None,
        "linkedin_url": profile.linkedin_url if profile else None,
        "city": profile.city if profile else None,
        "country": profile.country if profile else None,
        "preferred_currency": profile.preferred_currency if profile else None,
        "hourly_rate_preference": profile.hourly_rate_preference if profile else None,
    }

    return UserProfileResponse.model_validate(response_data)
