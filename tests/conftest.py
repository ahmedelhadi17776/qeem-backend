"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/qeem")


@pytest.fixture(scope="session")
def engine(database_url):
    """Create database engine for testing."""
    return create_engine(database_url)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create database session for testing."""
    from app.models.base import Base
    
    # Create all tables for this test session
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Clean up: delete all data and drop tables
        session.rollback()
        session.close()
        
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=engine)


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


@pytest.fixture(scope="function")
def sample_user(db_session, test_user_data):
    """Create a sample user for testing."""
    from app.services.user_service import UserService
    from app.schemas.auth import UserRegisterRequest

    user_service = UserService(db_session)

    # Create user
    register_data = UserRegisterRequest(
        email=test_user_data["email"],
        password=test_user_data["password"],
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"]
    )

    user = user_service.create_user(register_data)

    # Update profile with additional data
    from app.schemas.auth import UserProfileUpdateRequest
    profile_update = UserProfileUpdateRequest(
        profession=test_user_data["profession"],
        experience_years=test_user_data["experience_years"],
        city=test_user_data["city"],
        country=test_user_data["country"]
    )

    user_service.update_user_profile(user.id, profile_update)

    return {
        "id": user.id,
        "email": user.email,
        "first_name": test_user_data["first_name"],
        "last_name": test_user_data["last_name"],
        "password": test_user_data["password"]
    }
