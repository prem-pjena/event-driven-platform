import json
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.future import select

from app.shared.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.services.event_publisher import publish_event
from app.core.logging import logger
from app.core.locks import acquire_lock, release_lock


print("🔥🔥 WORKER IMAGE VERSION: 2026-02-10-UUID-GUARD-FINAL 🔥🔥")


# ==================================================
# Helpers
# ==================================================
def _parse_uuid(value: str) -> str | None:
    """
    Validates and normalizes UUID input.

    Returns:
        str(UUID) if valid
        None if invalid
    """
    try:
        return str(uuid.UUID(value))
    except Exception:
        return None


# ==================================================
# Core business logic
# ==================================================
async def process_payment(payment_id: str):
    """
    Async, Lambda-safe payment processor.
    """

    from app.workers.db.session import create_session_factory

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
                await charge(payment.amount)

                payment.status = PaymentStatus.SUCCESS
                payment.processed_at = datetime.utcnow()
                await session.commit()

                logger.info(
                    "PAYMENT_SUCCESS",
                    extra={
                        "payment_id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                    },
                )

                await publish_event(
                    "payment.success",
                    {
                        "event_id": str(uuid.uuid4()),
                        "payment_id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "occurred_at": payment.processed_at.isoformat(),
                    },
                )

            except PaymentGatewayError:
                await session.rollback()

                payment.status = PaymentStatus.FAILED
                payment.processed_at = datetime.utcnow()
                await session.commit()

                logger.info(
                    "PAYMENT_FAILED",
                    extra={"payment_id": str(payment.id)},
                )

                await publish_event(
                    "payment.failed",
                    {
                        "event_id": str(uuid.uuid4()),
                        "payment_id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "occurred_at": payment.processed_at.isoformat(),
                    },
                )

    finally:
        await release_lock(f"payment:{payment_id}", lock_token)
        await engine.dispose()


# ==================================================
# SQS processing
# ==================================================
async def handle_record(record: dict):
    try:
        body = json.loads(record["body"])
    except Exception:
        logger.warning("SQS_MESSAGE_INVALID_JSON", extra={"record": record})
        return

    raw_payment_id = None

    if isinstance(body, dict):
        raw_payment_id = body.get("payment_id")

    if not raw_payment_id and isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:
                return

        if isinstance(detail, dict):
            raw_payment_id = detail.get("payment_id")

    if not raw_payment_id:
        logger.warning("SQS_MESSAGE_MISSING_PAYMENT_ID", extra={"body": body})
        return

    payment_id = _parse_uuid(str(raw_payment_id))
    if not payment_id:
        logger.error(
            "SQS_MESSAGE_INVALID_PAYMENT_ID",
            extra={"payment_id": raw_payment_id},
        )
        # ACK the message – poison payload
        return

    await process_payment(payment_id)


async def process_event(event: dict):
    for record in event.get("Records", []):
        try:
            await handle_record(record)
        except Exception:
            # Catch-all to avoid SQS retry storms
            logger.exception("SQS_RECORD_PROCESSING_FAILED")


def handler(event, context):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(process_event(event))
    return {"status": "ok"}
