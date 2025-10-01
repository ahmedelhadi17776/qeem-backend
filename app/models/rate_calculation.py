"""Rate calculation models."""

from enum import Enum
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, Boolean
from sqlalchemy.orm import relationship

from .base import Base, IDMixin, TimestampMixin


class ProjectType(str, Enum):
    """Types of freelance projects."""
    WEB_DEVELOPMENT = "web_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    DESIGN = "design"
    WRITING = "writing"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    DATA_ANALYSIS = "data_analysis"
    OTHER = "other"


class ProjectComplexity(str, Enum):
    """Project complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class RateCalculation(Base, IDMixin, TimestampMixin):
    """Rate calculation results and inputs."""

    __tablename__ = "rate_calculations"

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)

    # Input Parameters
    project_type = Column(String(50), nullable=False)
    project_complexity = Column(String(50), nullable=False)
    estimated_hours = Column(Integer, nullable=False)
    experience_years = Column(Integer, nullable=False)
    skills_count = Column(Integer, nullable=False)
    location = Column(String(100), nullable=False)

    # Calculated Results
    minimum_rate = Column(Float, nullable=False)  # in EGP
    competitive_rate = Column(Float, nullable=False)  # in EGP
    premium_rate = Column(Float, nullable=False)  # in EGP

    # Additional Data
    # rule_based, ml_prediction
    calculation_method = Column(
        String(50), default="rule_based", nullable=False)
    confidence_score = Column(Float, nullable=True)  # for ML predictions
    reasoning = Column(Text, nullable=True)  # JSON string with breakdown

    # User Preferences
    preferred_rate = Column(Float, nullable=True)  # user's chosen rate
    is_favorite = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="rate_calculations")
