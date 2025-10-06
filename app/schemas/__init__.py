"""Pydantic schemas for request/response models."""

from .auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    UserResponse,
)
from .common import HealthResponse
from .market import (
    MarketStatisticsItem,
    MarketStatisticsQuery,
    MarketStatisticsResponse,
    MarketTrendsPoint,
    MarketTrendsQuery,
    MarketTrendsResponse,
)
from .rates import RateHistoryResponse, RateRequest, RateResponse

__all__ = [
    # Auth schemas
    "TokenResponse",
    "UserLoginRequest",
    "UserProfileResponse",
    "UserProfileUpdateRequest",
    "UserRegisterRequest",
    "UserResponse",
    # Common schemas
    "HealthResponse",
    # Market schemas
    "MarketStatisticsItem",
    "MarketStatisticsQuery",
    "MarketStatisticsResponse",
    "MarketTrendsPoint",
    "MarketTrendsQuery",
    "MarketTrendsResponse",
    # Rate schemas
    "RateHistoryResponse",
    "RateRequest",
    "RateResponse",
]
