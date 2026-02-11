from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, UUID as UUIDType

from app.shared.models import Payment, PaymentStatus
from app.db.models.outbox import OutboxEvent
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
    await db.flush()  # 🔥 ensures payment.id exists

    # --------------------------------------------------
    # Build domain event (PURE)
    # --------------------------------------------------
    event = payment_created_event(payment)

    # 🔒 HARD GUARARDS (VALID NOW)
    assert event["event_id"]
    assert event["event_type"]
    assert event["version"] is not None
    assert event["occurred_at"]

    # --------------------------------------------------
    # OUTBOX WRITE (ATOMIC 🔒)
    # --------------------------------------------------
    outbox = OutboxEvent(
        event_id=UUIDType(event["event_id"]),   # ✅ CAST TO UUID
        aggregate_id=payment.id,
        event_type=event["event_type"],
        version=event["version"],
        payload=event["payload"],
        occurred_at=event["occurred_at"],       # ✅ REQUIRED FIELD
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
    try:
        redis = await get_redis()
        if redis:
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
