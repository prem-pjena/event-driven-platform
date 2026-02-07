from typing import TypedDict
from datetime import datetime


class PaymentEvent(TypedDict):
    """
    Canonical event contract for all payment-related events.

    This structure is shared between:
    - API (producer)
    - Workers (consumers)
    - Analytics
    - Notifications

    Changing this is a BREAKING change.
    """

    event_id: str
    event_type: str        # payment.created | payment.success | payment.failed
    payment_id: str
    user_id: str
    amount: int
    currency: str
    occurred_at: str       # ISO timestamp
