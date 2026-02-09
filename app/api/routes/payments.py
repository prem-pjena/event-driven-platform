from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
import logging

from app.services.event_publisher import publish_event

logger = logging.getLogger(__name__)

router = APIRouter()


# ----------- Schemas -----------

class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str


# ----------- Route -----------

@router.post("", status_code=202)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    publish_event(
        event_type="payment.created.v1",
        payload={
            "user_id": str(payload.user_id),
            "amount": payload.amount,
            "currency": payload.currency,
            "idempotency_key": idempotency_key,
        },
    )

    return {
        "status": "accepted",
        "idempotency_key": idempotency_key,
    }
