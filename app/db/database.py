"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError

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


class TransactionManager:
    """Transaction manager for handling database transactions with automatic rollback."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None
        self._savepoint = None
    
    async def __aenter__(self):
        """Start a transaction."""
        self._transaction = await self.session.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction based on exceptions."""
        if exc_type is not None:
            # Exception occurred, rollback
            await self.session.rollback()
            return False
        
        # No exception, commit
        try:
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
    
    async def create_savepoint(self, name: str):
        """Create a savepoint for nested transactions."""
        if self._transaction is None:
            raise RuntimeError("No active transaction")
        self._savepoint = await self.session.begin_nested()
        return self._savepoint
    
    async def rollback_to_savepoint(self):
        """Rollback to the last savepoint."""
        if self._savepoint is None:
            raise RuntimeError("No savepoint to rollback to")
        await self._savepoint.rollback()
        self._savepoint = None


@asynccontextmanager
async def get_transaction_manager(session: AsyncSession):
    """Get a transaction manager for the given session."""
    async with TransactionManager(session) as tx_manager:
        yield tx_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for request scope."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
