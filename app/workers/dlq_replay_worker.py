import json
import os
import boto3
from app.core.logging import logger

sqs = boto3.client("sqs")
eventbridge = boto3.client("events")

DLQ_URL = os.environ["DLQ_URL"]
EVENT_BUS = os.environ.get("EVENT_BUS_NAME", "default")

ALLOWED_EVENTS = {
    "payment.success.v1",
    "payment.failed.v1"
}

MAX_BATCH = 10


def handler(event, context):
    logger.info("DLQ_REPLAY_TRIGGERED")

    response = sqs.receive_message(
        QueueUrl=DLQ_URL,
        MaxNumberOfMessages=MAX_BATCH,
        WaitTimeSeconds=1
    )

    messages = response.get("Messages", [])
    if not messages:
        logger.info("DLQ_EMPTY")
        return {"status": "empty"}

    for msg in messages:
        try:
            body = json.loads(msg["Body"])
            detail_type = body.get("detail-type")

            if detail_type not in ALLOWED_EVENTS:
                logger.warning(
                    "DLQ_SKIP_NON_TERMINAL_EVENT",
                    extra={"detail_type": detail_type}
                )
                # ❗ DELETE IT — poison message
                sqs.delete_message(
                    QueueUrl=DLQ_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
                continue

            logger.info(
                "DLQ_REPLAY_ATTEMPT",
                extra={
                    "event_id": body.get("id"),
                    "detail_type": detail_type,
                    "replayed": True
                }
            )

            result = eventbridge.put_events(
                Entries=[{
                    "Source": body["source"],
                    "DetailType": body["detail-type"],
                    "Detail": json.dumps(body["detail"]),
                    "EventBusName": EVENT_BUS
                }]
            )

            if result["FailedEntryCount"] > 0:
                raise RuntimeError("EventBridge publish failed")

            sqs.delete_message(
                QueueUrl=DLQ_URL,
                ReceiptHandle=msg["ReceiptHandle"]
            )

            logger.info("DLQ_REPLAY_SUCCESS")

        except Exception as exc:
            logger.error(
                "DLQ_REPLAY_FAILED",
                extra={
                    "error": str(exc),
                    "message_id": msg.get("MessageId")
                }
            )
