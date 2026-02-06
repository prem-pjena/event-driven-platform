from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.db.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.services.event_publisher import publish_event
from app.core.logging import logger
from datetime import datetime
import uuid


async def process_payment(payment_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        # Payment not found → safe no-op
        if not payment:
            return

        # Idempotency guard (protects against retries / duplicates)
        if payment.status != PaymentStatus.PENDING:
            return

        try:
            # -------------------------
            # External call (may fail)
            # -------------------------
            await charge(payment.amount)

            # -------------------------
            # Terminal SUCCESS state
            # -------------------------
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
                    "processing_time_sec": (
                        payment.processed_at - payment.created_at
                    ).total_seconds(),
                },
            )

            # -------------------------
            # Emit success event (best-effort)
            # -------------------------
            try:
                await publish_event(
                    "payment.success",
                    {
                        "event_id": str(uuid.uuid4()),
                        "payment_id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                    },
                )
            except Exception as exc:
                logger.error(
                    "PAYMENT_EVENT_PUBLISH_FAILED",
                    extra={
                        "payment_id": str(payment.id),
                        "event_type": "payment.success",
                        "error": str(exc),
                    },
                )

        except PaymentGatewayError:
            # -------------------------
            # Terminal FAILURE state
            # -------------------------
            payment.status = PaymentStatus.FAILED
            payment.processed_at = datetime.utcnow()
            await session.commit()

            logger.info(
                "PAYMENT_FAILED",
                extra={
                    "payment_id": str(payment.id),
                    "user_id": str(payment.user_id),
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "processing_time_sec": (
                        payment.processed_at - payment.created_at
                    ).total_seconds(),
                },
            )

            # -------------------------
            # Emit failure event (best-effort)
            # -------------------------
            try:
                await publish_event(
                    "payment.failed",
                    {
                        "event_id": str(uuid.uuid4()),
                        "payment_id": str(payment.id),
                        "user_id": str(payment.user_id),
                        "amount": payment.amount,
                        "currency": payment.currency,
                    },
                )
            except Exception as exc:
                logger.error(
                    "PAYMENT_EVENT_PUBLISH_FAILED",
                    extra={
                        "payment_id": str(payment.id),
                        "event_type": "payment.failed",
                        "error": str(exc),
                    },
                )

            # Re-raise → triggers SQS/Lambda retry
            raise


# AWS behavior mapping:
# - Gateway failure → payment worker retried
# - Event publish failure → logged & observable
# - Payment state remains immutable
# - Notifications & analytics are eventually consistent
