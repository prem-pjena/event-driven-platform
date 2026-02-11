from sqlalchemy import select
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.db.session import create_worker_session_factory
from app.db.models.outbox import OutboxEvent
from app.services.event_publisher import publish_event
from app.core.logging import logger

BATCH_SIZE = 10


async def run_outbox_publisher():
    """
    Publishes domain events from the outbox table.

    Guarantees:
    - Ordered delivery (occurred_at ASC)
    - At-least-once publishing
    - Exactly-once intent (event_id as idempotency key)
    - Safe concurrent execution (SELECT … FOR UPDATE SKIP LOCKED)
    - Lambda-safe resource cleanup
    """

    engine, SessionLocal = create_worker_session_factory()

    try:
        async with SessionLocal() as session:  # type: AsyncSession

            async with session.begin():
                result = await session.execute(
                    select(OutboxEvent)
                    .where(OutboxEvent.published_at.is_(None))
                    .order_by(OutboxEvent.occurred_at.asc())
                    .limit(BATCH_SIZE)
                    .with_for_update(skip_locked=True)
                )

                events = result.scalars().all()

                if not events:
                    logger.info("OUTBOX_EMPTY")
                    return {"status": "empty"}

                published_count = 0

                for event in events:
                    try:
                        # ✅ CORRECT KEYWORD CALL
                        publish_event(
                            event_type=event.event_type,
                            version=str(event.version),
                            payload={
                                **event.payload,
                                "event_id": str(event.event_id),
                                "event_type": event.event_type,
                                "version": event.version,
                                "occurred_at": event.occurred_at.isoformat(),
                                "replayed": False,
                            },
                            event_id=str(event.event_id),
                        )

                        event.published_at = datetime.now(timezone.utc)
                        published_count += 1

                        logger.info(
                            "OUTBOX_EVENT_PUBLISHED",
                            extra={
                                "event_id": str(event.event_id),
                                "event_type": event.event_type,
                                "aggregate_id": str(event.aggregate_id),
                            },
                        )

                    except Exception as exc:
                        logger.exception(
                            "OUTBOX_EVENT_PUBLISH_FAILED",
                            extra={
                                "event_id": str(event.event_id),
                                "event_type": event.event_type,
                                "error": str(exc),
                            },
                        )
                        # Do NOT mark published

                return {
                    "status": "processed",
                    "published_count": published_count,
                }

    finally:
        await engine.dispose()


# --------------------------------------------------
# 🔥 Lambda Entrypoint
# --------------------------------------------------
def handler(event, context):
    """
    AWS Lambda entrypoint.
    Fully executes async publisher.
    """
    return asyncio.run(run_outbox_publisher())
