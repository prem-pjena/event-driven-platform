import os
import json
import logging
import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Environment config
# --------------------------------------------------
USE_AWS_EVENTS = os.getenv("USE_AWS_EVENTS", "false").lower() == "true"
EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "default")


def get_eventbridge_client():
    """
    Create EventBridge client lazily.
    Safe for Lambda + VPC.
    """
    return boto3.client("events")


# --------------------------------------------------
# Event Publisher (API-SAFE + CONTRACT-SAFE ✅)
# --------------------------------------------------
def publish_event(event_type: str, payload: dict) -> None:
    """
    🔒 API-SAFE domain event publisher

    Guarantees:
    - NEVER raises
    - NEVER blocks API response
    - Enforces event contract (payment_id)
    - Best-effort delivery
    """

    logger.info(
        "EVENT_PUBLISH_ENTERED",
        extra={
            "event_type": event_type,
            "bus": EVENT_BUS_NAME,
            "enabled": USE_AWS_EVENTS,
        },
    )

    # --------------------------------------------------
    # HARD CONTRACT CHECK (CRITICAL FIX 🔥)
    # --------------------------------------------------
    payment_id = payload.get("payment_id")

    if not payment_id:
        logger.error(
            "EVENT_PUBLISH_DROPPED_MISSING_PAYMENT_ID",
            extra={
                "event_type": event_type,
                "payload": payload,
            },
        )
        return  # 🔒 swallow by design

    if not USE_AWS_EVENTS:
        logger.info(
            "EVENT_PUBLISH_SKIPPED_LOCAL",
            extra={"event_type": event_type},
        )
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
            logger.error(
                "EVENT_PUBLISH_FAILED",
                extra={
                    "event_type": event_type,
                    "response": response,
                },
            )
            return

        logger.info(
            "EVENT_PUBLISH_SUCCESS",
            extra={
                "event_type": event_type,
                "payment_id": payment_id,
            },
        )

    except (ClientError, BotoCoreError) as exc:
        logger.error(
            "EVENT_PUBLISH_AWS_EXCEPTION_SWALLOWED",
            extra={
                "event_type": event_type,
                "payment_id": payment_id,
                "error": str(exc),
            },
        )

    except Exception as exc:
        logger.error(
            "EVENT_PUBLISH_UNKNOWN_EXCEPTION_SWALLOWED",
            extra={
                "event_type": event_type,
                "payment_id": payment_id,
                "error": str(exc),
            },
        )

    return
