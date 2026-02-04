from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.idempotency import check_idempotency
from app.services.payment_service import create_payment
from app.services.event_publisher import publish_event
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

router = APIRouter()

# ----------- Schemas -----------

class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str


class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount: int
    currency: str
    status: str
    idempotency_key: str
    created_at: datetime

    class Config:
        orm_mode = True


# ----------- DB Dependency -----------

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ----------- Route -----------

@router.post("/", response_model=PaymentResponse)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    print("🔥 CREATE PAYMENT HANDLER HIT")

    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    existing = await check_idempotency(db, idempotency_key)
    if existing:
        return existing

    payment = await create_payment(
        db,
        payload.user_id,
        payload.amount,
        payload.currency,
        idempotency_key
    )

    await publish_event(
        "payment.created.v1",
        {
            "payment_id": str(payment.id),
            "amount": payment.amount,
            "user_id": str(payment.user_id),
        }
    )

    return payment
