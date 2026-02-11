from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.models import Payment
from app.core.redis import get_redis
from app.core.logging import logger

IDEMPOTENCY_TTL_SECONDS = 300


async def check_idempotency(
    session: AsyncSession,
    idempotency_key: str,
):
    redis = None
    try:
        redis = await get_redis()
    except Exception as exc:
        logger.warning(
            "REDIS_CLIENT_INIT_FAILED",
            extra={"error": str(exc)},
        )

    # -------------------------
    # Redis fast path
    # -------------------------
    if redis:
        try:
            payment_id = await redis.get(f"idempotency:{idempotency_key}")
            if payment_id:
                result = await session.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                return result.scalar_one_or_none()
        except Exception as exc:
            logger.warning(
                "REDIS_IDEMPOTENCY_FAILED",
                extra={"error": str(exc)},
            )

    # -------------------------
    # DB fallback
    # -------------------------
    result = await session.execute(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    payment = result.scalar_one_or_none()

    # -------------------------
    # Redis backfill
    # -------------------------
    if payment and redis:
        try:
            await redis.setex(
                f"idempotency:{idempotency_key}",
                IDEMPOTENCY_TTL_SECONDS,
                str(payment.id),
            )
        except Exception:
            pass

    return payment
