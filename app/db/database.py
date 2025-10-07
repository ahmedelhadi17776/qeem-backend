"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from ..core.config import get_settings

settings = get_settings()


def _create_engine_url() -> str:
    """Convert sync database URL to async URL."""
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


def _engine_connect_args(url: str) -> dict:
    """Get connection arguments for async engine."""
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _engine_pool_class(url: str):
    """Get pool class for async engine."""
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

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for request scope."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
