import json
import uuid
import asyncio
from datetime import datetime
from sqlalchemy.future import select

from app.shared.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.services.event_publisher import publish_event
from app.core.logging import logger


print("🔥🔥 WORKER IMAGE VERSION: 2026-02-09-FINAL-SCHEMA-TOLERANT 🔥🔥")


# ==================================================
# Core business logic
# ==================================================
async def process_payment(payment_id: str):
    """
    Async, Lambda-safe payment processor.
    """

    # 🔥 Import inside function (Lambda-safe)
    from app.workers.db.session import create_session_factory

    engine, SessionLocal = create_session_factory()

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

                publish_event(
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

                publish_event(
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
        await engine.dispose()


# ==================================================
# SQS processing (SCHEMA-TOLERANT ✅)
# ==================================================
async def handle_record(record: dict):
    """
    Handles ONE SQS record.
    Accepts ALL EventBridge → SQS shapes (raw + transformed).
    """

    try:
        body = json.loads(record["body"])
    except Exception:
        logger.warning("SQS_MESSAGE_INVALID_JSON", extra={"record": record})
        return

    payment_id = None

    # --------------------------------------------------
    # CASE 1: input_transformer → direct payload
    # --------------------------------------------------
    if isinstance(body, dict):
        payment_id = body.get("payment_id")

    # --------------------------------------------------
    # CASE 2: raw EventBridge envelope
    # --------------------------------------------------
    if not payment_id and isinstance(body, dict):
        detail = body.get("detail")

        # EventBridge often sends detail as STRING
        if isinstance(detail, str):
            try:
                detail = json.loads(detail)
            except Exception:
                logger.warning(
                    "SQS_DETAIL_JSON_PARSE_FAILED",
                    extra={"detail": detail},
                )
                return

        if isinstance(detail, dict):
            payment_id = (
                detail.get("payment_id")
                or detail.get("id")
                or detail.get("payment", {}).get("id")
            )

    if not payment_id:
        logger.warning(
            "SQS_MESSAGE_MISSING_PAYMENT_ID",
            extra={"body": body},
        )
        return

    await process_payment(str(payment_id))


async def process_event(event: dict):
    """
    Processes SQS batch WITHOUT failing the whole batch.
    """
    for record in event.get("Records", []):
        try:
            await handle_record(record)
        except Exception as exc:
            logger.exception(
                "SQS_RECORD_PROCESSING_FAILED",
                extra={
                    "error": str(exc),
                    "record": record,
                },
            )


# ==================================================
# Lambda entrypoint (IMAGE-SAFE)
# ==================================================
def handler(event, context):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(process_event(event))
    return {"status": "ok"}
