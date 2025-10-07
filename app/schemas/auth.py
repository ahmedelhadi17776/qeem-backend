"""Authentication schemas for request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )
    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User last name"
    )


class UserLoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""
    
    email: EmailStr = Field(..., description="User email address")


class UserResponse(BaseModel):
    """User response schema."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    created_at: datetime = Field(..., description="User creation timestamp")

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """User profile update request schema."""

    first_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User first name"
    )
    last_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User last name"
    )
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    profession: Optional[str] = Field(
        None, max_length=100, description="User profession"
    )
    experience_years: Optional[int] = Field(
        None, ge=0, le=50, description="Years of experience"
    )
    skills: Optional[str] = Field(None, description="User skills (JSON string)")
    portfolio_url: Optional[str] = Field(
        None, max_length=500, description="Portfolio URL"
    )
    linkedin_url: Optional[str] = Field(
        None, max_length=500, description="LinkedIn URL"
    )
    city: Optional[str] = Field(None, max_length=100, description="User city")
    country: Optional[str] = Field(None, max_length=100, description="User country")
    preferred_currency: Optional[str] = Field(
        None, max_length=3, description="Preferred currency"
    )
    hourly_rate_preference: Optional[int] = Field(
        None, ge=0, description="Hourly rate preference in EGP"
    )


class UserProfileResponse(BaseModel):
    """Extended user response with profile information."""

    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    created_at: datetime = Field(..., description="User creation timestamp")

    # Profile fields (from UserProfile)
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    phone: Optional[str] = Field(None, description="User phone number")
    bio: Optional[str] = Field(None, description="User bio")
    profession: Optional[str] = Field(None, description="User profession")
    experience_years: Optional[int] = Field(None, description="Years of experience")
    skills: Optional[str] = Field(None, description="User skills (JSON string)")
    portfolio_url: Optional[str] = Field(None, description="Portfolio URL")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn URL")
    city: Optional[str] = Field(None, description="User city")
    country: Optional[str] = Field(None, description="User country")
    preferred_currency: Optional[str] = Field(None, description="Preferred currency")
    hourly_rate_preference: Optional[int] = Field(
        None, description="Hourly rate preference in EGP"
    )

    class Config:
        from_attributes = True
