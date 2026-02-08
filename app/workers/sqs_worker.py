import json
import asyncio
from typing import Any, Dict

from app.core.logging import logger
from app.workers.payment_worker import process_payment
from app.workers.notification_worker import process_notification

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-08-SQS-HANDLER-FINAL 🔥🔥")


async def _handle_records(event: Dict[str, Any]):
    """
    Async SQS worker.
    Runs entirely inside ONE asyncio event loop.
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
                extra={
                    "event_type": event_type,
                    "detail": detail,
                },
            )

            if event_type == "payment.created.v1":
                payment_id = detail.get("payment_id")
                if not payment_id:
                    raise ValueError("payment_id missing")

                await process_payment(payment_id)

            elif event_type == "payment.success":
                await process_notification("payment.success", detail)

            elif event_type == "payment.failed":
                await process_notification("payment.failed", detail)

            else:
                logger.warning(
                    "UNHANDLED_EVENT_TYPE",
                    extra={"event_type": event_type},
                )

        except Exception as exc:
            logger.exception(
                "SQS_MESSAGE_FAILED",
                extra={"error": str(exc)},
            )
            raise  # SQS retry / DLQ


def handler(event: Dict[str, Any], context):
    """
    AWS Lambda entrypoint (SYNC).

    asyncio.run():
    - creates ONE loop
    - runs async logic
    - closes loop safely
    """

    try:
        asyncio.run(_handle_records(event))
    except Exception as exc:
        logger.exception(
            "SQS_BATCH_FAILED",
            extra={"error": str(exc)},
        )
        raise

    return {"status": "ok"}
