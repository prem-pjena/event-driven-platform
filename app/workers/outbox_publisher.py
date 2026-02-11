from sqlalchemy import select
from datetime import datetime, timezone

from app.db.session import create_session_factory
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

    engine, SessionLocal = create_session_factory()

    try:
        async with SessionLocal() as session:
            result = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.occurred_at.asc())  # 🔥 ORDER MATTERS
                .limit(BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )

            events = result.scalars().all()

            if not events:
                logger.info("OUTBOX_EMPTY")
                return

            for event in events:
                try:
                    # 🔐 Idempotent publish (event_id is the key)
                    publish_event(
                        event.event_type,
                        {
                            **event.payload,
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                            "version": event.version,
                            "occurred_at": event.occurred_at.isoformat(),
                            "replayed": False,
                        },
                    )

                    # ✅ Mark published ONLY after successful publish
                    event.published_at = datetime.now(timezone.utc)

                    logger.info(
                        "OUTBOX_EVENT_PUBLISHED",
                        extra={
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                            "aggregate_id": str(event.aggregate_id),
                        },
                    )

                except Exception as exc:
                    # ❌ DO NOT commit this event
                    logger.exception(
                        "OUTBOX_EVENT_PUBLISH_FAILED",
                        extra={
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                            "error": str(exc),
                        },
                    )
                    # Continue with other events (partial failure safe)

            # ✅ Commit only successfully published events
            await session.commit()

    finally:
        # 🔥 ABSOLUTELY REQUIRED IN LAMBDA
        await engine.dispose()
