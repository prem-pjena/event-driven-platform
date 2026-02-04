import logging

logger = logging.getLogger(__name__)

async def publish_event(event_type: str, payload: dict):
    logger.info(
        "EVENT_PUBLISHED",
        extra={
            "event_type": event_type,
            "payload": payload
        }
    )
