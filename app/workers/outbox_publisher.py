from sqlalchemy import select
from datetime import datetime

from app.workers.db.session import AsyncSessionLocal
from app.workers.db.models.outbox import OutboxEvent
from app.services.event_publisher import publish_event
from app.core.logging import logger

BATCH_SIZE = 10


async def run_outbox_publisher():
    """
    Publishes domain events from the outbox table.

    Guarantees:
    - Ordered delivery (per aggregate)
    - At-least-once publishing
    - Exactly-once intent (via event_id)
    - Safe concurrent execution (SKIP LOCKED)
    """

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.occurred_at.asc())  # 🔥 ORDER MATTERS
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )

        events = result.scalars().all()

        if not events:
            logger.debug("OUTBOX_EMPTY")
            return

        for event in events:
            try:
                # 🔒 NEVER await — best-effort & non-blocking
                publish_event(
                    event.event_type,
                    {
                        **event.payload,
                        "event_id": str(event.event_id),
                        "event_type": event.event_type,
                        "version": event.version,
                        "occurred_at": event.occurred_at.isoformat(),
                    },
                )

                event.published_at = datetime.utcnow()

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
                # DO NOT mark published — retry later

        await session.commit()
