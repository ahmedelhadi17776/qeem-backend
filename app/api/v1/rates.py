from fastapi import APIRouter, Depends
from ...services.rates import calculate_compensation_tiers
from ...schemas.rates import RateRequest, RateResponse, RateHistoryResponse
from ..deps import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/history", response_model=RateHistoryResponse)
async def get_history() -> RateHistoryResponse:
    return RateHistoryResponse(items=[])


@router.post("/calculate", response_model=RateResponse)
async def calculate_rate(
    payload: RateRequest, db: Session = Depends(get_db)
) -> RateResponse:
    """Calculate rate tiers based on a simple rule-based engine.

    This endpoint returns minimum, competitive, and premium rates in EGP.
    """
    # TODO: Get user_id from authentication when auth is implemented
    user_id = None  # Will be replaced with actual user authentication
    tiers = calculate_compensation_tiers(payload, db=db, user_id=user_id)
    return RateResponse(
        minimum_rate=tiers["minimum_rate"],
        competitive_rate=tiers["competitive_rate"],
        premium_rate=tiers["premium_rate"],
        currency=tiers["currency"],
        method=tiers["method"],
        rationale=(
            "Rule-based calculation using project complexity, experience, "
            "skills, client region, and urgency."
        )
    )
