import pandas as pd
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.db.models import Payment, PaymentStatus, DailyPaymentAnalytics
from datetime import date

async def run_daily_analytics():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Payment))
        payments = result.scalars().all()

        if not payments:
            return

        df = pd.DataFrame([{
            "status": p.status.value,
            "created_at": p.created_at.date()
        } for p in payments])

        today = date.today()
        today_df = df[df["created_at"] == today]

        total = len(today_df)
        success = len(today_df[today_df["status"] == "SUCCESS"])
        failed = len(today_df[today_df["status"] == "FAILED"])

        failure_rate = failed / total if total > 0 else 0

        analytics = DailyPaymentAnalytics(
            date=today,
            total_payments=total,
            successful_payments=success,
            failed_payments=failed,
            failure_rate=failure_rate
        )

        session.add(analytics)
        await session.commit()
