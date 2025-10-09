"""Pydantic schemas for rate calculation requests and responses."""

from typing import Literal, Annotated, Optional

from pydantic import BaseModel, Field
from typing import List


class RateRequest(BaseModel):
    project_type: Literal[
        "web_development",
        "mobile_development",
        "design",
        "writing",
        "marketing",
        "consulting",
        "data_analysis",
        "other",
    ] = Field(..., description="Type of project")
    project_complexity: Literal["simple", "moderate", "complex", "enterprise"]
    estimated_hours: Annotated[int, Field(gt=0, le=2000)] = Field(
        ..., description="Estimated hours"
    )
    experience_years: Annotated[int, Field(ge=0, le=50)] = Field(
        ..., description="Years of experience"
    )
    skills_count: Annotated[int, Field(ge=0, le=100)] = Field(
        ..., description="Number of relevant skills"
    )
    location: str = Field(..., description="Primary work location (city, country)")
    client_region: Literal["egypt", "mena", "europe", "usa", "global"] = "egypt"
    urgency: Literal["normal", "rush"] = "normal"


class RateResponse(BaseModel):
    minimum_rate: Annotated[float, Field(ge=0)]  # EGP/hour
    competitive_rate: Annotated[float, Field(ge=0)]  # EGP/hour
    premium_rate: Annotated[float, Field(ge=0)]  # EGP/hour
    currency: Literal["EGP"] = "EGP"
    method: Literal["rule_based", "ml_prediction"] = "rule_based"
    rationale: str = Field(
        default=(
            "Rule-based calculation using project complexity, experience, "
            "skills, client region, and urgency."
        )
    )
    # Optional ML-specific fields
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0-1), only for ML predictions",
    )
    model_version: Optional[str] = Field(
        default=None, description="ML model version, only for ML predictions"
    )


class RateHistoryResponse(BaseModel):
    items: List[RateResponse] = Field(
        default_factory=list, description="List of previous rate calculations"
    )
