from fastapi import APIRouter
from ...services.rates import calculate_compensation_tiers
from ...schemas.rates import RateRequest, RateResponse

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/history")
async def get_history() -> dict:
    return {"items": []}


@router.post("/calculate", response_model=RateResponse)
async def calculate_rate(payload: RateRequest) -> RateResponse:
    """Calculate rate tiers based on a simple rule-based engine.

    This endpoint returns minimum, competitive, and premium rates in EGP.
    """
    tiers = calculate_compensation_tiers(payload)
    return RateResponse(**tiers)
