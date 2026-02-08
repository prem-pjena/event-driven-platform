import asyncio
from sqlalchemy.future import select

from app.core.logging import logger
from app.db.session import create_session_factory
from app.db.event_models import ProcessedEvent


class NotificationError(Exception):
    pass


async def send_email(user_id: str, message: str):
    await asyncio.sleep(1)
    logger.info("EMAIL_SENT", extra={"user_id": user_id, "message": message})


async def send_sms(user_id: str, message: str):
    await asyncio.sleep(0.5)
    logger.info("SMS_SENT", extra={"user_id": user_id, "message": message})


async def process_notification(event_type: str, payload: dict):
    engine, SessionLocal = create_session_factory()

    try:
        event_id = payload["event_id"]
        user_id = payload["user_id"]
        amount = payload["amount"]
        currency = payload["currency"]
        payment_id = payload["payment_id"]

        async with SessionLocal() as session:
            result = await session.execute(
                select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
            )
            if result.scalar_one_or_none():
                logger.info(
                    "DUPLICATE_NOTIFICATION_EVENT",
                    extra={"event_id": event_id, "payment_id": payment_id},
                )
                return

            session.add(ProcessedEvent(event_id=event_id))
            await session.commit()

        if event_type == "payment.success":
            message = f"Your payment of {amount} {currency} was successful."
        elif event_type == "payment.failed":
            message = f"Your payment of {amount} {currency} failed."
        else:
            logger.warning("UNKNOWN_NOTIFICATION_EVENT", extra={"event_type": event_type})
            return

        await asyncio.gather(
            send_email(user_id, message),
            send_sms(user_id, message),
        )

        logger.info(
            "NOTIFICATION_SENT",
            extra={
                "event_id": event_id,
                "payment_id": payment_id,
                "user_id": user_id,
                "event_type": event_type,
            },
        )

    except Exception as exc:
        logger.error(
            "NOTIFICATION_FAILED",
            extra={"event_id": event_id, "error": str(exc)},
        )
        raise NotificationError("Notification delivery failed") from exc

    finally:
        await engine.dispose()
