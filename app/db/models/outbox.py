from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.shared.base import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔒 External immutable event id
    event_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    # 🔑 Aggregate (payment_id)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)

    event_type = Column(String, nullable=False)
    version = Column(Integer, nullable=False)

    payload = Column(JSON, nullable=False)

    # 🔥 IMPORTANT FOR REPLAY / AUDIT (must be timezone aware)
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # ✅ FIXED — timezone aware
    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
