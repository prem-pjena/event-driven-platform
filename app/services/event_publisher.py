import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Environment-based switch
# --------------------------------------------------
USE_AWS = os.getenv("USE_AWS_EVENTS", "false").lower() == "true"
EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "default")

# Lazy client (safe for Lambda cold starts)
_eventbridge_client = None


def get_eventbridge_client():
    global _eventbridge_client
    if _eventbridge_client is None:
        _eventbridge_client = boto3.client("events")
    return _eventbridge_client


# --------------------------------------------------
# Event Publisher
# --------------------------------------------------
async def publish_event(event_type: str, payload: dict):
    """
    Publishes domain events.

    Local:
      - Logs event only

    AWS:
      - Sends event to EventBridge
    """

    # Always log (observability)
    logger.info(
        "EVENT_PUBLISHED",
        extra={
            "event_type": event_type,
            "payload": payload,
            "aws_enabled": USE_AWS,
        },
    )

    # ----------------------------------------------
    # Local mode (no AWS)
    # ----------------------------------------------
    if not USE_AWS:
        return

    # ----------------------------------------------
    # AWS EventBridge mode
    # ----------------------------------------------
    try:
        client = get_eventbridge_client()

        response = client.put_events(
            Entries=[
                {
                    "Source": "event-platform.payments",
                    "DetailType": event_type,
                    "Detail": json.dumps(payload),
                    "EventBusName": EVENT_BUS_NAME,
                }
            ]
        )

        if response.get("FailedEntryCount", 0) > 0:
            logger.error(
                "EVENTBRIDGE_PUBLISH_PARTIAL_FAILURE",
                extra={"response": response},
            )
            raise RuntimeError("EventBridge publish failed")

    except ClientError as exc:
        logger.error(
            "EVENTBRIDGE_PUBLISH_ERROR",
            extra={
                "event_type": event_type,
                "error": str(exc),
            },
        )
        raise
