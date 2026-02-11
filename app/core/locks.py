import uuid
import logging
from typing import Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

LOCK_TTL = 30


async def acquire_lock(name: str) -> Optional[str]:
    redis_client = await get_redis()

    if not redis_client:
        logger.warning("LOCK_REDIS_UNAVAILABLE")
        return None

    token = str(uuid.uuid4())

    acquired = await redis_client.set(
        name=f"lock:{name}",
        value=token,
        nx=True,
        ex=LOCK_TTL,
    )

    if acquired:
        logger.info("LOCK_ACQUIRED", extra={"name": name})
        return token

    logger.info("LOCK_ALREADY_HELD", extra={"name": name})
    return None


async def release_lock(name: str, token: str) -> None:
    redis_client = await get_redis()

    if not redis_client or not token:
        return

    lua = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """

    try:
        await redis_client.eval(lua, 1, f"lock:{name}", token)
        logger.info("LOCK_RELEASED", extra={"name": name})
    except Exception:
        logger.exception("LOCK_RELEASE_FAILED")
