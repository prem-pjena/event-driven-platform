from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.payment_service import create_payment
from app.workers.idempotency import check_idempotency
from app.core.rate_limit import rate_limit

router = APIRouter()


class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str


@router.post("", status_code=202)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    allowed = await rate_limit(str(payload.user_id))
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")

    existing = await check_idempotency(db, idempotency_key)
    if existing:
        return {
            "status": "accepted",
            "payment_id": str(existing.id),
            "idempotency_key": idempotency_key,
        }

    payment = await create_payment(
        db=db,
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=idempotency_key,
    )

    return {
        "status": "accepted",
        "payment_id": str(payment.id),
        "idempotency_key": idempotency_key,
    }
