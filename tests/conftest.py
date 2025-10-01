"""Test configuration and fixtures."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

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
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
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
