from fastapi import APIRouter, Depends
from ...services.rates import calculate_compensation_tiers
from ...schemas.rates import RateRequest, RateResponse, RateHistoryResponse
from ...database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/history", response_model=RateHistoryResponse)
async def get_history() -> RateHistoryResponse:
    return RateHistoryResponse(items=[])


@router.post("/calculate", response_model=RateResponse)
async def calculate_rate(payload: RateRequest, db: Session = Depends(get_db)) -> RateResponse:
    """Calculate rate tiers based on a simple rule-based engine.

    This endpoint returns minimum, competitive, and premium rates in EGP.
    """
    tiers = calculate_compensation_tiers(payload)
    return RateResponse(**tiers)
