"""Contract model."""

from enum import Enum

from sqlalchemy import Column, ForeignKey, String, Text, Float, Boolean, Date, Integer
from sqlalchemy.orm import relationship

from .base import Base, IDMixin, TimestampMixin


class ContractStatus(str, Enum):
    """Contract status options."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class ContractType(str, Enum):
    """Contract type options."""

    HOURLY = "hourly"
    FIXED_PRICE = "fixed_price"
    RETAINER = "retainer"
    MILESTONE = "milestone"


class Contract(Base, IDMixin, TimestampMixin):
    """Contract model for freelancer agreements."""

    __tablename__ = "contracts"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Contract Details
    contract_number = Column(String(50), unique=True,
                             nullable=False, index=True)
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(255), nullable=True)
    project_title = Column(String(300), nullable=False)
    project_description = Column(Text, nullable=True)

    # Contract Type and Terms
    contract_type = Column(String(20), nullable=False)
    hourly_rate = Column(Float, nullable=True)  # for hourly contracts
    fixed_price = Column(Float, nullable=True)  # for fixed price contracts
    retainer_amount = Column(Float, nullable=True)  # for retainer contracts
    currency = Column(String(3), default="EGP", nullable=False)

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    estimated_hours = Column(Float, nullable=True)

    # Status and Terms
    status = Column(String(20), default=ContractStatus.DRAFT, nullable=False)
    payment_terms = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)  # JSON string
    milestones = Column(Text, nullable=True)  # JSON string

    # Legal and Files
    terms_and_conditions = Column(Text, nullable=True)
    contract_pdf_path = Column(String(500), nullable=True)
    signed_by_client = Column(Boolean, default=False, nullable=False)
    signed_by_freelancer = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="contracts")
