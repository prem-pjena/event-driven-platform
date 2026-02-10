from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.shared.models import Payment, PaymentStatus
from app.workers.db.models.outbox import OutboxEvent
from app.events.payment_events import payment_created_event
from app.core.redis import get_redis
from app.core.logging import logger


async def create_payment(
    db: AsyncSession,
    user_id: UUID,
    amount: int,
    currency: str,
    idempotency_key: str,
):
    # --------------------------------------------------
    # Create Payment (PENDING)
    # --------------------------------------------------
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        idempotency_key=idempotency_key,
        status=PaymentStatus.PENDING,
    )

    db.add(payment)

    # 🔥 REQUIRED: ensures payment.id exists
    await db.flush()

    # --------------------------------------------------
    # Build domain event (PURE, NO I/O)
    # --------------------------------------------------
    event = payment_created_event(payment)

    # 🔒 HARD GUARARDS (FAANG STYLE)
    assert event.event_id, "event_id must be set"
    assert event.version is not None, "event version must be set"

    # --------------------------------------------------
    # OUTBOX WRITE (ATOMIC 🔒)
    # --------------------------------------------------
    outbox = OutboxEvent(
        event_id=event.event_id,
        aggregate_id=payment.id,
        event_type=event.event_type,
        version=event.version,
        payload=event.payload,
    )

    db.add(outbox)

    # --------------------------------------------------
    # Commit payment + event TOGETHER
    # --------------------------------------------------
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(payment)

    # --------------------------------------------------
    # Redis write-through (BEST EFFORT)
    # --------------------------------------------------
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
