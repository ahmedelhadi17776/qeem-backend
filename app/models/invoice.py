"""Invoice model."""

from enum import Enum
from sqlalchemy import Column, ForeignKey, String, Text, Float, Date, Integer
from sqlalchemy.orm import relationship

from .base import Base, IDMixin, TimestampMixin


class InvoiceStatus(str, Enum):
    """Invoice status options."""

    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base, IDMixin, TimestampMixin):
    """Invoice model for freelancer billing."""

    __tablename__ = "invoices"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Invoice Details
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(255), nullable=True)
    client_address = Column(Text, nullable=True)

    # Financial Information
    subtotal = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="EGP", nullable=False)

    # Dates
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)

    # Status and Notes
    status = Column(String(20), default=InvoiceStatus.DRAFT, nullable=False)
    notes = Column(Text, nullable=True)
    payment_terms = Column(Text, nullable=True)

    # File References
    pdf_path = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="invoices")
