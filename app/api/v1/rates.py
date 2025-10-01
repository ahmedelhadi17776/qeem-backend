from fastapi import APIRouter

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get("/history")
async def get_history() -> dict:
    return {"items": []}
