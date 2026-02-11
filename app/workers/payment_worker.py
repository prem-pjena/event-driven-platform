import uuid
import asyncio
import json
from datetime import datetime, timezone
from sqlalchemy.future import select

from app.shared.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.core.logging import logger
from app.core.locks import acquire_lock, release_lock
from app.db.models.outbox import OutboxEvent
from app.db.session import create_worker_session_factory

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-11-FINAL-PROD 🔥🔥")


# --------------------------------------------------
# Core business logic
# --------------------------------------------------
async def process_payment(payment_id: str):
    """
    Production-grade payment processor.

    Guarantees:
    - idempotent
    - distributed locked
    - atomic state + outbox write
    - safe DB cleanup
    """

    engine, SessionLocal = create_worker_session_factory()

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

                processed_time = datetime.now(timezone.utc)

                payment.status = PaymentStatus.SUCCESS
                payment.processed_at = processed_time

                # -----------------------------
                # Atomic OUTBOX event
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
                            "occurred_at": processed_time.isoformat(),
                        },
                        occurred_at=processed_time,
                    )
                )

                await session.commit()

                logger.info(
                    "PAYMENT_SUCCESS",
                    extra={"payment_id": str(payment.id)},
                )

            except PaymentGatewayError:
                await session.rollback()

                processed_time = datetime.now(timezone.utc)

                payment.status = PaymentStatus.FAILED
                payment.processed_at = processed_time

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
                            "occurred_at": processed_time.isoformat(),
                        },
                        occurred_at=processed_time,
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


# --------------------------------------------------
# Lambda batch processor
# --------------------------------------------------
async def run_worker(event):
    records = event.get("Records", [])

    for record in records:
        try:
            body = json.loads(record["body"])
            detail = body.get("detail", {})
            payment_id = detail.get("payment_id")

            if not payment_id:
                logger.warning("MISSING_PAYMENT_ID")
                continue

            await process_payment(payment_id)

        except Exception as exc:
            logger.exception("WORKER_RECORD_FAILED", extra={"error": str(exc)})


# --------------------------------------------------
# REQUIRED Lambda entrypoint
# --------------------------------------------------
def handler(event, context):
    return asyncio.run(run_worker(event))
