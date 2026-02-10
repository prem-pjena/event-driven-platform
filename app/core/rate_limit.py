import logging
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

RATE_LIMIT = 10
WINDOW_SECONDS = 60


async def rate_limit(key: str) -> bool:
    """
    Redis-based rate limiter.
    FAILS OPEN if Redis is unavailable.
    """
    redis = await get_redis()
    if not redis:
        logger.warning("RATE_LIMIT_REDIS_UNAVAILABLE")
        return True  # 🔥 FAIL OPEN

    redis_key = f"rate:{key}"

    try:
        current = await redis.incr(redis_key)

        if current == 1:
            await redis.expire(redis_key, WINDOW_SECONDS)

        if current > RATE_LIMIT:
            logger.info(
                "RATE_LIMIT_EXCEEDED",
                extra={"key": key, "count": current},
            )
            return False

        return True

    except Exception as exc:
        logger.error(
            "RATE_LIMIT_ERROR",
            extra={"error": str(exc)},
        )
        return True  # 🔥 FAIL OPEN
