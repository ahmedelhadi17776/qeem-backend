from fastapi import APIRouter

from . import auth, rates, market, users, audit

api_router = APIRouter(prefix="/api/v1")

# Include all sub-routers
api_router.include_router(auth.router)
api_router.include_router(rates.router)
api_router.include_router(market.router)
api_router.include_router(users.router)
api_router.include_router(audit.router)
