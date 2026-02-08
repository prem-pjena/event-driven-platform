import json
import asyncio
from typing import Any, Dict

from app.core.logging import logger
from app.workers.notification_worker import process_notification

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-08-SQS-HANDLER-LAMBDA-SAFE 🔥🔥")


def handler(event: Dict[str, Any], context):
    """
    Lambda entrypoint (MUST be sync).
    """
    records = event.get("Records", [])

    logger.info(
        "SQS_BATCH_RECEIVED",
        extra={"record_count": len(records)},
    )

    for record in records:
        try:
            body = json.loads(record["body"])

            event_type = body.get("detail-type")
            detail = body.get("detail", {})

            logger.info(
                "SQS_EVENT_RECEIVED",
                extra={"event_type": event_type},
            )

            if event_type == "payment.success":
                asyncio.run(process_notification("payment.success", detail))

            elif event_type == "payment.failed":
                asyncio.run(process_notification("payment.failed", detail))

            else:
                logger.warning(
                    "UNHANDLED_EVENT_TYPE",
                    extra={"event_type": event_type},
                )

        except Exception as exc:
            logger.exception(
                "SQS_EVENT_PROCESSING_FAILED",
                extra={"error": str(exc)},
            )
            # 🔥 Triggers retry / DLQ
            raise

    return {"status": "ok"}
