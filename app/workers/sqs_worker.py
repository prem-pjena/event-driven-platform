import json
import asyncio
from typing import Any, Dict

from app.core.logging import logger
from app.events.schema import EventEnvelope
from app.workers.payment_worker import process_payment
from app.workers.notification_worker import process_notification

print("🔥🔥 WORKER IMAGE VERSION: 2026-02-10-OUTBOX-V1-SAFE 🔥🔥")


# ==================================================
# Core async handler
# ==================================================
async def _handle_records(event: Dict[str, Any]):
    records = event.get("Records", [])

    logger.info(
        "SQS_BATCH_RECEIVED",
        extra={"record_count": len(records)},
    )

    for record in records:
        try:
            raw_body = record.get("body")
            if not raw_body:
                raise ValueError("Empty SQS body")

            body = json.loads(raw_body)

            # ------------------------------------------
            # STRICT event schema validation (🔥 PHASE 4)
            # ------------------------------------------
            event_envelope = EventEnvelope.model_validate(body)

            event_type = event_envelope.event_type
            version = event_envelope.version
            payload = event_envelope.payload

            logger.info(
                "DOMAIN_EVENT_RECEIVED",
                extra={
                    "event_type": event_type,
                    "version": version,
                    "event_id": str(event_envelope.event_id),
                },
            )

            # ------------------------------------------
            # VERSIONED routing (🔥 CRITICAL)
            # ------------------------------------------
            if event_type == "payment.created" and version == 1:
                payment_id = payload.get("payment_id")
                if not payment_id:
                    raise ValueError("payment_id missing in payload")

                await process_payment(payment_id)

            elif event_type == "payment.success" and version == 1:
                await process_notification("payment.success", payload)

            elif event_type == "payment.failed" and version == 1:
                await process_notification("payment.failed", payload)

            else:
                logger.warning(
                    "UNSUPPORTED_EVENT_VERSION",
                    extra={
                        "event_type": event_type,
                        "version": version,
                    },
                )

        except Exception as exc:
            logger.exception(
                "SQS_RECORD_PROCESSING_FAILED",
                extra={"error": str(exc)},
            )
            # 🔥 Force retry / DLQ
            raise


# ==================================================
# Lambda entrypoint (SYNC)
# ==================================================
def handler(event: Dict[str, Any], context):
    try:
        asyncio.run(_handle_records(event))
    except Exception as exc:
        logger.exception(
            "SQS_BATCH_FAILED",
            extra={"error": str(exc)},
        )
        raise

    return {"status": "ok"}
