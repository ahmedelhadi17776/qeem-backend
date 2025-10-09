from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
async def calculate_rate_endpoint(
    request: RateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate freelance rate tiers based on project details.
    This endpoint uses A/B testing: a percentage of users will receive
    ML-based predictions, while others receive rule-based calculations.
    """
    # A/B test: 10% of users get ML predictions (users with ID ending in 0)
    use_ml = (current_user.id % 10) == 0

    result_dict = await calculate_compensation_tiers(
        payload=request, db=db, user_id=current_user.id, use_ml=use_ml
    )
    return RateResponse(**result_dict)
