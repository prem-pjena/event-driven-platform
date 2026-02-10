import os
import logging
import redis.asyncio as redis
from typing import Optional

logger = logging.getLogger(__name__)

_redis: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """
    Lambda-safe, lazy Redis getter.
    Returns None if Redis is unavailable.
    """
    global _redis

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("REDIS_URL_NOT_SET")
        return None

    if _redis is not None:
        return _redis

    try:
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

        # 🔥 Validate connection ONCE
        await client.ping()

        _redis = client
        logger.info("REDIS_CONNECTED")

        return _redis

    except Exception as exc:
        logger.error(
            "REDIS_CONNECTION_FAILED",
            extra={"error": str(exc)},
        )
        _redis = None
        return None
