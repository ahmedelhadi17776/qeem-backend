from typing import Annotated, cast, Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.rate_limit_deps import rates_calculate_rate_limit
from ...models.user import User
from ...schemas.rates import RateRequest, RateResponse, RateHistoryResponse
from ...services.rates import calculate_compensation_tiers, get_user_rate_history
from ..deps import get_db, get_current_active_user

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/history", response_model=RateHistoryResponse)
async def get_history(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> RateHistoryResponse:
    """Get rate calculation history for the current user."""
    items = await get_user_rate_history(db, int(current_user.id))
    return RateHistoryResponse(items=items)


@router.post("/calculate", response_model=RateResponse)
async def calculate_rate(
    payload: RateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rates_calculate_rate_limit),
) -> RateResponse:
    """Calculate rate tiers based on a simple rule-based engine.

    This endpoint returns minimum, competitive, and premium rates in EGP.
    Requires authentication to save calculation history.
    """
    # Use authenticated user ID
    tiers = await calculate_compensation_tiers(
        payload, db=db, user_id=int(current_user.id)
    )
    return RateResponse(
        minimum_rate=float(tiers["minimum_rate"]),
        competitive_rate=float(tiers["competitive_rate"]),
        premium_rate=float(tiers["premium_rate"]),
        currency=cast("Literal['EGP']", tiers["currency"]),
        method=cast("Literal['rule_based']", tiers["method"]),
        rationale=(
            "Rule-based calculation using project complexity, experience, "
            "skills, client region, and urgency."
        ),
    )
