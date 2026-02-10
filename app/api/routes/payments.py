from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.db.session import get_session
from app.services.payment_service import create_payment
from app.workers.idempotency import check_idempotency
from app.core.rate_limit import rate_limit

router = APIRouter()


# -------------------------
# Request schema
# -------------------------
class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str


# -------------------------
# API Endpoint
# -------------------------
@router.post("", status_code=202)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    # -------------------------
    # Rate limiting (best-effort)
    # -------------------------
    allowed = await rate_limit(str(payload.user_id))
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    # -------------------------
    # Idempotency guard
    # -------------------------
    existing = await check_idempotency(db, idempotency_key)
    if existing:
        return {
            "status": "accepted",
            "payment_id": str(existing.id),
            "idempotency_key": idempotency_key,
        }

    # -------------------------
    # Atomic write (Payment + Outbox)
    # -------------------------
    payment = await create_payment(
        db=db,
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=idempotency_key,
    )

    # -------------------------
    # 202 Accepted (durable)
    # -------------------------
    return {
        "status": "accepted",
        "payment_id": str(payment.id),
        "idempotency_key": idempotency_key,
    }
