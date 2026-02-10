from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from typing import Optional
import logging

from app.services.event_publisher import publish_event
from app.core.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str


@router.post("", status_code=202)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    allowed = await rate_limit(str(payload.user_id))
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    # 🔥 Command ID (required for event-driven systems)
    payment_id = str(uuid4())

    try:
        publish_event(
            event_type="payment.created.v1",
            payload={
                "payment_id": payment_id,          # 🔥 REQUIRED
                "user_id": str(payload.user_id),
                "amount": payload.amount,
                "currency": payload.currency,
                "idempotency_key": idempotency_key,
            },
        )
    except Exception as exc:
        # 🔥 FAIL-OPEN (API should not die)
        logger.error(
            "EVENT_PUBLISH_FAILED",
            extra={"error": str(exc)},
        )

    return {
        "status": "accepted",
        "payment_id": payment_id,
        "idempotency_key": idempotency_key,
    }
