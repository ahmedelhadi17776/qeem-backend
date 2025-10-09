"""Rule-based rate calculation service.

This module contains a simple, transparent rule engine to compute
minimum, competitive, and premium hourly rates in EGP based on:
 - Project complexity
 - Years of experience
 - Number of relevant skills
 - Client region (Egypt, MENA, Europe, USA, Global)
 - Urgency (normal vs rush)
"""

from typing import Dict, Optional, List, cast, Literal, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.rates import RateRequest, RateResponse
from ..repositories.rate_repository import RateRepository
from ..infra.metrics import record_rate_calculation
from ..services.audit_service import AuditService
from ..services.ml_prediction import MLPredictionService
from ..core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class RateCalculationResult(TypedDict, total=False):
    """Type definition for rate calculation result."""

    minimum_rate: float
    competitive_rate: float
    premium_rate: float
    currency: Literal["EGP"]
    method: Literal["rule_based", "ml_prediction"]
    confidence_score: float  # Optional, only for ML predictions
    model_version: str  # Optional, only for ML predictions


# Initialize ML service as a singleton
_ml_service: Optional[MLPredictionService] = None


def get_ml_service() -> Optional[MLPredictionService]:
    """Get a singleton instance of the MLPredictionService."""
    global _ml_service
    settings = get_settings()
    if settings.enable_ml_predictions and _ml_service is None:
        try:
            _ml_service = MLPredictionService(model_path=settings.ml_model_path)
            if not _ml_service.is_available():
                _ml_service = None
                raise FileNotFoundError("ML model loaded but is not available.")
        except FileNotFoundError:
            logger.warning(
                f"ML model file not found at {settings.ml_model_path}. "
                "Falling back to rule-based calculations."
            )
            _ml_service = None
    return _ml_service


def _base_rate_for_project_type(project_type: str) -> float:
    """Return a baseline hourly rate in EGP by project type.

    Values are placeholders to enable the MVP and should be replaced later
    with market-backed figures or ML predictions.
    """
    baselines: Dict[str, float] = {
        "web_development": 250.0,
        "mobile_development": 280.0,
        "design": 220.0,
        "writing": 180.0,
        "marketing": 200.0,
        "consulting": 300.0,
        "data_analysis": 260.0,
        "other": 200.0,
    }
    return baselines.get(project_type, 200.0)


def _complexity_multiplier(complexity: str) -> float:
    """Get complexity multiplier for rate calculation."""
    return {
        "simple": 0.9,
        "moderate": 1.0,
        "complex": 1.2,
        "enterprise": 1.4,
    }.get(complexity, 1.0)


def _experience_multiplier(years: int) -> float:
    """Get experience multiplier for rate calculation."""
    if years < 1:
        return 0.8
    if years < 3:
        return 0.9
    if years < 5:
        return 1.0
    if years < 8:
        return 1.15
    return 1.3


def _skills_multiplier(skills_count: int) -> float:
    """Get skills multiplier for rate calculation."""
    if skills_count <= 2:
        return 0.95
    if skills_count <= 5:
        return 1.0
    if skills_count <= 8:
        return 1.08
    return 1.15


def _client_region_multiplier(region: str) -> float:
    """Get client region multiplier for rate calculation."""
    return {
        "egypt": 1.0,
        "mena": 1.1,
        "europe": 1.8,
        "usa": 2.0,
        "global": 1.6,
    }.get(region, 1.0)


def _urgency_multiplier(urgency: str) -> float:
    """Get urgency multiplier for rate calculation."""
    return 1.15 if urgency == "rush" else 1.0


async def calculate_compensation_tiers(
    payload: RateRequest,
    db: Optional[AsyncSession] = None,
    user_id: Optional[int] = None,
    use_ml: bool = True,
) -> RateCalculationResult:
    """Compute hourly rate tiers in EGP.

    If use_ml=True and ML model is available, use ML prediction.
    Otherwise, fall back to rule-based calculation.
    """
    settings = get_settings()
    result: RateCalculationResult = {}

    # Try ML prediction first if enabled
    if use_ml and settings.enable_ml_predictions:
        ml_service = get_ml_service()
        if ml_service and ml_service.is_available():
            try:
                ml_result = ml_service.predict_rate(payload)
                # Cast to RateCalculationResult
                result = cast(RateCalculationResult, ml_result)
                logger.info(f"Used ML prediction for user {user_id}")
            except Exception as e:
                logger.error(
                    f"ML prediction failed for user {user_id}: {e}. "
                    "Falling back to rules."
                )
                result = {}  # Clear result to ensure fallback

    # Fall back to rule-based calculation if ML is disabled, fails, or is not used
    if not result:
        base = _base_rate_for_project_type(payload.project_type)
        value = (
            base
            * _complexity_multiplier(payload.project_complexity)
            * _experience_multiplier(int(payload.experience_years))
            * _skills_multiplier(int(payload.skills_count))
            * _client_region_multiplier(payload.client_region)
            * _urgency_multiplier(payload.urgency)
        )

        # ensure a sensible lower bound
        minimum_rate = round(max(80.0, value * 0.8))
        competitive_rate = round(value)
        premium_rate = round(value * 1.3)

        result = {
            "minimum_rate": float(minimum_rate),
            "competitive_rate": float(competitive_rate),
            "premium_rate": float(premium_rate),
            "currency": "EGP",
            "method": "rule_based",
        }
        logger.info(f"Used rule-based calculation for user {user_id}")

    # Save calculation to database if session and user_id are provided
    if db and user_id:
        rate_repo = RateRepository(db)
        calculation_data = {
            "user_id": user_id,
            "project_type": payload.project_type,
            "project_complexity": payload.project_complexity,
            "estimated_hours": payload.estimated_hours,
            "experience_years": payload.experience_years,
            "skills_count": payload.skills_count,
            "location": payload.location,
            "minimum_rate": result.get("minimum_rate"),
            "competitive_rate": result.get("competitive_rate"),
            "premium_rate": result.get("premium_rate"),
            "calculation_method": result.get("method", "rule_based"),
            "confidence_score": result.get("confidence_score"),
        }
        await rate_repo.create(calculation_data)

        # Record metrics
        record_rate_calculation(
            payload.project_type,
            payload.project_complexity,
            method=str(result.get("method", "rule_based")),
        )

        # Log audit trail
        audit_service = AuditService(db)
        audit_service.log_action_async(
            user_id=user_id,
            action="rate_calculation",
            resource_type="rate_calculation",
            resource_id=str(calculation_data.get("id", "pending")),
            new_values={
                "project_type": payload.project_type,
                "project_complexity": payload.project_complexity,
                "estimated_hours": payload.estimated_hours,
                "experience_years": payload.experience_years,
                "minimum_rate": result.get("minimum_rate"),
                "competitive_rate": result.get("competitive_rate"),
                "premium_rate": result.get("premium_rate"),
            },
            success=True,
        )

    return result


async def get_user_rate_history(db: AsyncSession, user_id: int) -> List[RateResponse]:
    """Get rate calculation history for a user.

    Args:
        db: Database session
        user_id: User ID to get history for

    Returns:
        List of RateResponse objects
    """
    rate_repo = RateRepository(db)
    calculations = await rate_repo.get_by_user_id(user_id)

    # Convert RateCalculation objects to RateResponse objects
    items = []
    for calc in calculations:
        items.append(
            RateResponse(
                minimum_rate=float(calc.minimum_rate),
                competitive_rate=float(calc.competitive_rate),
                premium_rate=float(calc.premium_rate),
                currency="EGP",
                method=cast("Literal['rule_based']", calc.calculation_method),
                rationale=str(
                    calc.reasoning
                    or "Rule-based calculation using project complexity, experience, "
                    "skills, client region, and urgency."
                ),
            )
        )

    return items
