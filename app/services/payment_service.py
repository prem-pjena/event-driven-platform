from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Payment, PaymentStatus
from uuid import UUID

async def create_payment(
    db: AsyncSession,   # ✅ CORRECT ARG NAME
    user_id: UUID,
    amount: int,
    currency: str,
    idempotency_key: str,
):
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        idempotency_key=idempotency_key,
        status=PaymentStatus.PENDING,  # ✅ ENUM SAFE
    )

    db.add(payment)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(payment)
    return payment
