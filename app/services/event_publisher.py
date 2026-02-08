import os
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Environment config
# --------------------------------------------------
USE_AWS_EVENTS = os.getenv("USE_AWS_EVENTS", "false").lower() == "true"
EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "default")

_eventbridge_client = None


def get_eventbridge_client():
    global _eventbridge_client
    if _eventbridge_client is None:
        _eventbridge_client = boto3.client("events")
    return _eventbridge_client


# --------------------------------------------------
# Event Publisher (SYNC BY DESIGN ✅)
# --------------------------------------------------
def publish_event(event_type: str, payload: dict) -> None:
    """
    Best-effort domain event publisher.

    Design guarantees:
    - SYNC function (safe with boto3)
    - Never awaited
    - Non-blocking in async flows
    - Raises only on hard AWS failure
    """

    logger.info(
        "EVENT_PUBLISH_ATTEMPT",
        extra={
            "event_type": event_type,
            "aws_enabled": USE_AWS_EVENTS,
        },
    )

    # Local / dev / tests
    if not USE_AWS_EVENTS:
        logger.info("EVENT_PUBLISH_SKIPPED_LOCAL")
        return

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
            raise RuntimeError(f"EventBridge failure: {response}")

        logger.info(
            "EVENT_PUBLISH_SUCCESS",
            extra={"event_type": event_type},
        )

    except ClientError as exc:
        logger.error(
            "EVENT_PUBLISH_ERROR",
            extra={"error": str(exc)},
        )
        raise
