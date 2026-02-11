import os
import logging
import redis.asyncio as redis
from typing import Optional

logger = logging.getLogger(__name__)


async def get_redis() -> Optional[redis.Redis]:
    """
    Lambda-safe Redis getter.

    - No global client reuse
    - No cross-event-loop contamination
    - Fails open if Redis unavailable
    """

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("REDIS_URL_NOT_SET")
        return None

    try:
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

        # Validate connection on each invocation
        await client.ping()

        return client

    except Exception as exc:
        logger.error(
            "REDIS_CONNECTION_FAILED",
            extra={"error": str(exc)},
        )
        return None
