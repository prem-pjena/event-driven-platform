from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Payment
from uuid import UUID

async def create_payment(
    session: AsyncSession,
    user_id: UUID,
    amount: int,
    currency: str,
    idempotency_key: str
):
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        idempotency_key=idempotency_key
    )

    session.add(payment)

    # 🔑 THESE TWO LINES FIX THE ISSUE
    await session.flush()   # sends INSERT
    await session.commit()  # commits transaction

    await session.refresh(payment)

    print("✅ PAYMENT INSERTED:", payment.id)

    return payment
