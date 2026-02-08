from sqlalchemy.future import select
from datetime import date

from app.db.session import create_session_factory
from app.db.models import Payment, DailyPaymentAnalytics


async def run_daily_analytics():
    import pandas as pd  # lazy import

    engine, SessionLocal = create_session_factory()

    try:
        async with SessionLocal() as session:
            result = await session.execute(select(Payment))
            payments = result.scalars().all()

            if not payments:
                return

            df = pd.DataFrame(
                [
                    {"status": p.status.value, "created_at": p.created_at.date()}
                    for p in payments
                ]
            )

            today = date.today()
            today_df = df[df["created_at"] == today]

            total = len(today_df)
            success = len(today_df[today_df["status"] == "SUCCESS"])
            failed = len(today_df[today_df["status"] == "FAILED"])

            analytics = DailyPaymentAnalytics(
                date=today,
                total_payments=total,
                successful_payments=success,
                failed_payments=failed,
                failure_rate=failed / total if total else 0,
            )

            session.add(analytics)
            await session.commit()

    finally:
        await engine.dispose()
