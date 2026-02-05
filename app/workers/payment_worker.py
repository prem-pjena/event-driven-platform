from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.db.models import Payment, PaymentStatus
from app.services.fake_gateway import charge, PaymentGatewayError


async def process_payment(payment_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        # Payment not found → safe no-op
        if not payment:
            return

        # Idempotency guard
        if payment.status != PaymentStatus.PENDING:
            return

        try:
            # External call (may fail)
            await charge(payment.amount)

            # Terminal success state
            payment.status = PaymentStatus.SUCCESS
            await session.commit()

        except PaymentGatewayError:
            # Terminal failure state MUST be persisted
            payment.status = PaymentStatus.FAILED
            await session.commit()

            # Re-raise to simulate SQS/Lambda retry
            raise
