"""Database configuration and session management."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import get_settings
from ..models.base import Base

settings = get_settings()


def _create_engine_url() -> str:
    return settings.database_url


def _engine_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _engine_pool_class(url: str):
    if url.startswith("sqlite"):
        return StaticPool
    return None


DATABASE_URL = _create_engine_url()

engine_kwargs = {
    "connect_args": _engine_connect_args(DATABASE_URL),
}
pool_class = _engine_pool_class(DATABASE_URL)
if pool_class is not None:
    engine_kwargs["poolclass"] = pool_class

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create all database tables. Use only in development."""
    if settings.environment == "development":
        Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
