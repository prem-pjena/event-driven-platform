from fastapi import APIRouter
from app.core.logging import logger

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/health", summary="Notifications liveness check")
async def notifications_health():
    """
    Liveness probe for notifications surface.

    This does NOT guarantee downstream workers are healthy.
    """
    logger.info("NOTIFICATIONS_HEALTH_CHECK")
    return {"status": "alive"}


@router.get("/ready", summary="Notifications readiness check")
async def notifications_ready():
    """
    Readiness probe.

    In future this can verify:
    - Redis connectivity
    - EventBridge permissions
    - DLQ backlog size
    """
    logger.info("NOTIFICATIONS_READINESS_CHECK")
    return {"status": "ready"}
