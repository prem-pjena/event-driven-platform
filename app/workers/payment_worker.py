import uuid
from datetime import datetime
from sqlalchemy.future import select

from app.shared.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.core.logging import logger
from app.core.locks import acquire_lock, release_lock
from app.db.models.outbox import OutboxEvent

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-10-PHASE4-OUTBOX-SAFE 🔥🔥")


async def process_payment(payment_id: str):
    """
    Phase 4–correct payment processor.

    Responsibilities:
    - idempotent
    - locked
    - updates DB state
    - writes OUTBOX events (NOT EventBridge)
    """

    from app.db.session import create_session_factory

    engine, SessionLocal = create_session_factory()

    lock_token = await acquire_lock(f"payment:{payment_id}")
    if not lock_token:
        logger.info("PAYMENT_LOCK_ALREADY_HELD", extra={"payment_id": payment_id})
        return

    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.warning("PAYMENT_NOT_FOUND", extra={"payment_id": payment_id})
                return

            if payment.status != PaymentStatus.PENDING:
                logger.info(
                    "PAYMENT_ALREADY_PROCESSED",
                    extra={
                        "payment_id": str(payment.id),
                        "status": payment.status.value,
                    },
                )
                return

            try:
                # -----------------------------
                # External side effect
                # -----------------------------
                await charge(payment.amount)

                payment.status = PaymentStatus.SUCCESS
                payment.processed_at = datetime.utcnow()

                # -----------------------------
                # OUTBOX EVENT (🔥 ATOMIC)
                # -----------------------------
                session.add(
                    OutboxEvent(
                        event_id=uuid.uuid4(),
                        aggregate_id=payment.id,
                        event_type="payment.success",
                        version=1,
                        payload={
                            "payment_id": str(payment.id),
                            "user_id": str(payment.user_id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "occurred_at": payment.processed_at.isoformat(),
                        },
                    )
                )

                await session.commit()

                logger.info(
                    "PAYMENT_SUCCESS",
                    extra={"payment_id": str(payment.id)},
                )

            except PaymentGatewayError:
                await session.rollback()

                payment.status = PaymentStatus.FAILED
                payment.processed_at = datetime.utcnow()

                session.add(
                    OutboxEvent(
                        event_id=uuid.uuid4(),
                        aggregate_id=payment.id,
                        event_type="payment.failed",
                        version=1,
                        payload={
                            "payment_id": str(payment.id),
                            "user_id": str(payment.user_id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "occurred_at": payment.processed_at.isoformat(),
                        },
                    )
                )

                await session.commit()

                logger.info(
                    "PAYMENT_FAILED",
                    extra={"payment_id": str(payment.id)},
                )

    finally:
        await release_lock(f"payment:{payment_id}", lock_token)
        await engine.dispose()
