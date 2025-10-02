"""Model tests for SQLAlchemy models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User, UserProfile, UserRole
from app.models.rate_calculation import RateCalculation, ProjectType, ProjectComplexity
from app.models.invoice import Invoice, InvoiceStatus
from app.models.contract import Contract, ContractStatus, ContractType
from app.models.market_statistics import MarketStatistics
from app.models.base import Base
from uuid import uuid4
from datetime import date

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """Create database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestUserModel:
    """Test User model."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        user = User(
            email=f"test_{uuid4().hex}@example.com",
            password_hash="hashed_password",
            role=UserRole.FREELANCER
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email.endswith("@example.com")
        assert user.role == UserRole.FREELANCER
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_profile_relationship(self, db_session):
        """Test user-profile relationship."""
        user = User(
            email=f"test_{uuid4().hex}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()  # Get user ID

        profile = UserProfile(
            user_id=user.id,
            first_name="Test",
            last_name="User",
            profession="Developer",
            experience_years=3,
            city="Cairo",
            country="Egypt"
        )
        db_session.add(profile)
        db_session.commit()

        assert user.profile is not None
        assert user.profile.first_name == "Test"
        assert profile.user.email.endswith("@example.com")


class TestRateCalculationModel:
    """Test RateCalculation model."""

    def test_create_rate_calculation(self, db_session):
        """Test creating a rate calculation."""
        user = User(
            email=f"test_{uuid4().hex}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()

        calculation = RateCalculation(
            user_id=user.id,
            project_type=ProjectType.WEB_DEVELOPMENT,
            project_complexity=ProjectComplexity.MODERATE,
            estimated_hours=40,
            experience_years=3,
            skills_count=5,
            location="Cairo, Egypt",
            minimum_rate=50.0,
            competitive_rate=75.0,
            premium_rate=100.0
        )
        db_session.add(calculation)
        db_session.commit()

        assert calculation.id is not None
        assert calculation.project_type == ProjectType.WEB_DEVELOPMENT
        assert calculation.minimum_rate == 50.0
        assert calculation.calculation_method == "rule_based"


class TestInvoiceModel:
    """Test Invoice model."""

    def test_create_invoice(self, db_session):
        """Test creating an invoice."""
        user = User(
            email=f"test_{uuid4().hex}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()

        invoice = Invoice(
            user_id=user.id,
            invoice_number="INV-001",
            client_name="Test Client",
            client_email="client@example.com",
            subtotal=1000.0,
            tax_rate=0.14,
            tax_amount=140.0,
            total_amount=1140.0,
            issue_date=date(2024, 1, 1),
            due_date=date(2024, 1, 15),
            status=InvoiceStatus.DRAFT
        )
        db_session.add(invoice)
        db_session.commit()

        assert invoice.id is not None
        assert invoice.invoice_number == "INV-001"
        assert invoice.total_amount == 1140.0
        assert invoice.status == InvoiceStatus.DRAFT


class TestContractModel:
    """Test Contract model."""

    def test_create_contract(self, db_session):
        """Test creating a contract."""
        user = User(
            email=f"test_{uuid4().hex}@example.com",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()

        contract = Contract(
            user_id=user.id,
            contract_number="CON-001",
            client_name="Test Client",
            project_title="Web Development Project",
            contract_type=ContractType.HOURLY,
            hourly_rate=75.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
            status=ContractStatus.DRAFT
        )
        db_session.add(contract)
        db_session.commit()

        assert contract.id is not None
        assert contract.contract_number == "CON-001"
        assert contract.contract_type == ContractType.HOURLY
        assert contract.hourly_rate == 75.0


class TestMarketStatisticsModel:
    """Test MarketStatistics model."""

    def test_create_market_statistics(self, db_session):
        """Test creating market statistics."""
        stats = MarketStatistics(
            date=date(2024, 1, 1),
            period_type="weekly",
            project_type="web_development",
            experience_level="mid",
            location="Cairo, Egypt",
            average_rate=75.0,
            median_rate=70.0,
            min_rate=50.0,
            max_rate=100.0,
            sample_size=100,
            data_source="upwork"
        )
        db_session.add(stats)
        db_session.commit()

        assert stats.id is not None
        assert stats.project_type == "web_development"
        assert stats.average_rate == 75.0
        assert stats.sample_size == 100
