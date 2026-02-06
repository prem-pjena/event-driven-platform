from sqlalchemy import Column, String, Integer, Enum, DateTime, Date, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()


# ------------------------
# Payment Status Enum
# ------------------------
class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ------------------------
# Payments Table
# ------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)

    status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    idempotency_key = Column(String, unique=True, nullable=False)

    # When payment request was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # When payment reached terminal state (SUCCESS / FAILED)
    processed_at = Column(DateTime, nullable=True)


# ------------------------
# Daily Analytics Table
# ------------------------
class DailyPaymentAnalytics(Base):
    __tablename__ = "daily_payment_analytics"

    date = Column(Date, primary_key=True)

    total_payments = Column(Integer, nullable=False)
    successful_payments = Column(Integer, nullable=False)
    failed_payments = Column(Integer, nullable=False)

    failure_rate = Column(Float, nullable=False)
    avg_processing_time_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
