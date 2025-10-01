"""User and UserProfile models."""

from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, String, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base, IDMixin, TimestampMixin


class UserRole(str, Enum):
    """User roles in the system."""
    FREELANCER = "freelancer"
    ADMIN = "admin"


class User(Base, IDMixin, TimestampMixin):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default=UserRole.FREELANCER, nullable=False)

    # Relationships
    profile = relationship("UserProfile", back_populates="user",
                           uselist=False, cascade="all, delete-orphan")
    rate_calculations = relationship(
        "RateCalculation", back_populates="user", cascade="all, delete-orphan")
    invoices = relationship(
        "Invoice", back_populates="user", cascade="all, delete-orphan")
    contracts = relationship(
        "Contract", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base, IDMixin, TimestampMixin):
    """Extended user profile information."""

    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)

    # Personal Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)

    # Professional Information
    profession = Column(String(100), nullable=True)
    experience_years = Column(Integer, nullable=True)
    skills = Column(Text, nullable=True)  # JSON string of skills list
    portfolio_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # Location
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="Egypt", nullable=False)

    # Preferences
    preferred_currency = Column(String(3), default="EGP", nullable=False)
    hourly_rate_preference = Column(Integer, nullable=True)  # in EGP

    # Relationships
    user = relationship("User", back_populates="profile")
