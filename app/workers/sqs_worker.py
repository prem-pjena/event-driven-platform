import json
from typing import Any, Dict

from app.core.logging import logger
from app.workers.notification_worker import process_notification

# ==========================================================
# SQS → Lambda handler
# ==========================================================
async def handler(event: Dict[str, Any], context):
    records = event.get("Records", [])

    logger.info(
        "SQS_BATCH_RECEIVED",
        extra={"record_count": len(records)},
    )

    for record in records:
        try:
            # SQS body is always a string
            body = json.loads(record["body"])

            # EventBridge envelope
            event_type = body.get("detail-type")
            detail = body.get("detail", {})

            logger.info(
                "SQS_EVENT_RECEIVED",
                extra={
                    "event_type": event_type,
                    "detail": detail,
                },
            )

            # -------------------------
            # Route by event type
            # -------------------------
            if event_type == "payment.success":
                await process_notification("payment.success", detail)

            elif event_type == "payment.failed":
                await process_notification("payment.failed", detail)

            else:
                logger.warning(
                    "UNHANDLED_EVENT_TYPE",
                    extra={"event_type": event_type},
                )

        except Exception as exc:
            # 🔥 IMPORTANT:
            # Raising here triggers SQS retry / DLQ
            logger.exception(
                "SQS_EVENT_PROCESSING_FAILED",
                extra={"error": str(exc)},
            )
            raise

    # Lambda requires JSON-serializable return
    return {"status": "ok"}
