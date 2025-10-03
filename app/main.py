"""Main FastAPI application."""

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .api.v1 import api_router
from .api.v1 import auth as auth_router
from .api.v1 import rates as rates_router
from .core.config import get_settings
from .db.database import create_tables
import os
from .schemas.common import HealthResponse
from .core.logging import (
    configure_logging,
    configure_uvicorn_json_logging,
)

try:
    import sentry_sdk  # type: ignore[import-not-found]
except Exception:
    sentry_sdk = None  # type: ignore[assignment]

# Load environment variables from .env file
load_dotenv()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    if sentry_sdk and (settings.sentry.dsn or os.getenv("SENTRY_DSN")):
        sentry_sdk.init(dsn=settings.sentry.dsn or os.getenv("SENTRY_DSN"))
    # configure logging (JSON; set LOG_LEVEL via env per environment)
    configure_logging(level=settings.log_level, fmt="json")
    configure_uvicorn_json_logging(settings.log_level)
    create_tables()
    yield
    # shutdown
    return


app = FastAPI(
    title="Qeem Backend",
    description="AI-powered freelance rate calculator for Egyptian freelancers",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


# Mount API v1 routers (include sub-routers before mounting to the app)
api_router.include_router(rates_router.router)
api_router.include_router(auth_router.router)
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional basic rate limiting middleware (MVP)
if settings.enable_rate_limiting:
    from .infra.redis import get_redis

    @app.middleware("http")
    # type: ignore[no-redef]
    async def rate_limit_middleware(request: Request, call_next):
        redis = get_redis()
        client_host = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_host}:{request.url.path}"
        current = redis.get(key)
        if current and int(str(current)) >= 100:
            return Response(status_code=429, content="Rate limit exceeded")
        if current:
            redis.incr(key)
        else:
            redis.setex(key, 3600, 1)
        return await call_next(request)
