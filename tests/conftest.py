"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

# Ensure project root is on sys.path so `import app` works when running from tests/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def database_url():
    """Get database URL from environment."""
    # Force SQLite for tests to avoid PostgreSQL connection issues
    # Override any DATABASE_URL from .env file
    return "sqlite+aiosqlite:///test.db"


@pytest.fixture(scope="session")
def engine(database_url):
    """Create async database engine for testing."""
    return create_async_engine(database_url, echo=False)


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Create async database session for testing."""
    from app.models.base import Base

    # Create all tables once for the session
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    AsyncSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Use a fake Redis during tests to avoid external dependency failures
class _FakeRedis:
    def __init__(self):
        self.store = {}
        self.ttl = {}

    def get(self, key: str):
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str):
        self.store[key] = value
        self.ttl[key] = ttl


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch):
    try:
        from app.services import market as market_service
        monkeypatch.setattr(market_service, "get_redis", lambda: _FakeRedis())
    except Exception:
        pass
    yield


@pytest.fixture(scope="function")
def test_user_data():
    """Sample user data for testing."""
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    return {
        "email": unique_email,
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "profession": "Software Developer",
        "experience_years": 3,
        "city": "Cairo",
        "country": "Egypt"
    }


@pytest.fixture(scope="function")
def test_rate_calculation_data():
    """Sample rate calculation data for testing."""
    return {
        "project_type": "web_development",
        "project_complexity": "moderate",
        "estimated_hours": 40,
        "experience_years": 3,
        "skills_count": 5,
        "location": "Cairo, Egypt"
    }


@pytest_asyncio.fixture(scope="function")
async def sample_user(db_session, test_user_data):
    """Create a sample user for testing."""
    from app.services.user_service import UserService
    from app.schemas.auth import UserRegisterRequest

    user_service = UserService(db_session)

    # Create user
    register_data = UserRegisterRequest(
        email=test_user_data.get("email"),
        password=test_user_data.get("password"),
        first_name=test_user_data.get("first_name"),
        last_name=test_user_data.get("last_name")
    )

    user = await user_service.create_user(register_data)

    # Update profile with additional data
    from app.schemas.auth import UserProfileUpdateRequest
    profile_update = UserProfileUpdateRequest(
        profession=test_user_data.get("profession"),
        experience_years=test_user_data.get("experience_years"),
        city=test_user_data.get("city"),
        country=test_user_data.get("country")
    )

    await user_service.update_user_profile(user.id, profile_update)

    return {
        "id": user.id,
        "email": test_user_data.get("email"),
        "first_name": test_user_data.get("first_name"),
        "last_name": test_user_data.get("last_name"),
        "password": test_user_data.get("password")
    }
