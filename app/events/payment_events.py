from typing import TypedDict
from datetime import datetime
from uuid import uuid4

from app.shared.models import Payment


class PaymentEvent(TypedDict):
    """
    Canonical event contract for all payment-related events.

    ⚠️ VERSIONED, STABLE CONTRACT
    Breaking changes require a NEW version.
    """

    event_id: str
    event_type: str        # payment.created.v1 | payment.success.v1 | payment.failed.v1
    payment_id: str
    user_id: str
    amount: int
    currency: str
    occurred_at: str       # ISO-8601


def payment_created_event(payment: Payment) -> PaymentEvent:
    """
    🔒 SINGLE SOURCE OF TRUTH for payment.created.v1
    """

    return PaymentEvent(
        event_id=str(uuid4()),
        event_type="payment.created.v1",
        payment_id=str(payment.id),
        user_id=str(payment.user_id),
        amount=payment.amount,
        currency=payment.currency,
        occurred_at=datetime.utcnow().isoformat(),
    )
