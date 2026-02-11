from typing import TypedDict, Dict, Any
from datetime import datetime
from uuid import uuid4

from app.shared.models import Payment


class DomainEvent(TypedDict):
    event_id: str
    event_type: str
    version: int
    payload: Dict[str, Any]
    occurred_at: str


def payment_created_event(payment: Payment) -> DomainEvent:
    """
    🔒 SINGLE SOURCE OF TRUTH for payment.created.v1
    """

    return {
        "event_id": str(uuid4()),
        "event_type": "payment.created.v1",
        "version": 1,
        "payload": {
            "payment_id": str(payment.id),
            "user_id": str(payment.user_id),
            "amount": payment.amount,
            "currency": payment.currency,
        },
        "occurred_at": datetime.utcnow().isoformat(),
    }
