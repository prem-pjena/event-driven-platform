from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter()

class PaymentRequest(BaseModel):
    user_id: UUID
    amount: int
    currency: str

@router.post("/")
async def create_payment(
    payload: PaymentRequest,
    idempotency_key: Optional[str] = Header(None)
):
    return {
        "message": "Payment received",
        "idempotency_key": idempotency_key,
        "status": "PENDING"
    }
