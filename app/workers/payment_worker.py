from sqlalchemy.future import select
from datetime import datetime
import uuid

from app.db.session import AsyncSessionLocal
from app.db.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError
from app.services.event_publisher import publish_event
from app.core.logging import logger

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-08-PAYMENT-WORKER-LAMBDA-SAFE 🔥🔥")


async def process_payment(payment_id: str):
    if AsyncSessionLocal is None:
        logger.error("DATABASE_NOT_CONFIGURED", extra={"payment_id": payment_id})
        raise RuntimeError("Database not configured")

    async with AsyncSessionLocal() as session:
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
                extra={"payment_id": payment_id, "status": payment.status.value},
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

            # ✅ SAFE: await event publishing
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
            payment.status = PaymentStatus.FAILED
            payment.processed_at = datetime.utcnow()
            await session.commit()

            logger.info(
                "PAYMENT_FAILED",
                extra={
                    "payment_id": str(payment.id),
                    "user_id": str(payment.user_id),
                },
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

            return
