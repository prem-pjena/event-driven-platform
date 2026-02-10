import os
import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError

EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "default")


def get_eventbridge_client():
    return boto3.client("events")


def publish_event(
    *,
    event_type: str,
    version: str,
    payload: dict,
    event_id: str,
) -> None:
    """
    LOW-LEVEL EventBridge publisher.
    Raises on failure.
    Used ONLY by outbox_publisher.
    """

    client = get_eventbridge_client()

    try:
        response = client.put_events(
            Entries=[
                {
                    "Source": "event-platform.payments",
                    "DetailType": f"{event_type}.{version}",
                    "Detail": json.dumps(payload),
                    "EventBusName": EVENT_BUS_NAME,
                }
            ]
        )

        if response.get("FailedEntryCount", 0) > 0:
            raise RuntimeError(
                f"EventBridge failed for event_id={event_id}"
            )

    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(
            f"EventBridge exception for event_id={event_id}: {exc}"
        ) from exc
