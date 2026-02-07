from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.core.idempotency import check_idempotency
from app.services.payment_service import create_payment

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

print("🔥🔥 API IMAGE VERSION: 2026-02-07-FINAL-LAMBDA-SAFE 🔥🔥")

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

    model_config = ConfigDict(from_attributes=True)

# ----------- DB Dependency -----------

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ----------- Route -----------

@router.post("", status_code=201)
async def create_payment_api(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    existing = await check_idempotency(db, idempotency_key)
    if existing:
        return PaymentResponse.model_validate(existing)

    payment = await create_payment(
        db=db,
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        idempotency_key=idempotency_key,
    )

    # ❌ DO NOT publish events from API Lambda
    # ✅ Event publishing must be done by worker / SQS

    return PaymentResponse.model_validate(payment)
