from sqlalchemy import select
from app.core.redis import get_redis
from app.shared.models import Payment

CACHE_TTL = 60


async def get_payment(db, payment_id):
    redis = get_redis()

    if redis:
        cached = await redis.get(f"payment:{payment_id}")
        if cached:
            return Payment.parse_raw(cached)

    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if payment and redis:
        await redis.setex(
            f"payment:{payment_id}",
            CACHE_TTL,
            payment.json(),
        )

    return payment
