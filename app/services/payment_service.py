from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.shared.models import Payment, PaymentStatus
from app.core.redis import get_redis
from app.core.logging import logger


async def create_payment(
    db: AsyncSession,
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
        status=PaymentStatus.PENDING,
    )

    db.add(payment)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(payment)

    # -------------------------
    # Redis write-through
    # -------------------------
    redis = get_redis()
    if redis:
        try:
            await redis.setex(
                f"idempotency:{idempotency_key}",
                300,
                str(payment.id),
            )
        except Exception as exc:
            logger.warning(
                "REDIS_IDEMPOTENCY_WRITE_FAILED",
                extra={"error": str(exc)},
            )

    return payment
