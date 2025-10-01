"""Main FastAPI application."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from .api.v1 import api_router
from .api.v1 import rates as rates_router
from .api.v1 import auth as auth_router
from .database import create_tables

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Qeem Backend",
    description="AI-powered freelance rate calculator for Egyptian freelancers",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    create_tables()


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "qeem-backend"}


# Mount API v1 routers
app.include_router(api_router)
api_router.include_router(rates_router.router)
api_router.include_router(auth_router.router)
