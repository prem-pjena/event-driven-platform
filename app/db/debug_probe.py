from sqlalchemy import text
from app.db.session import create_session_factory
from app.core.logging import logger


async def probe_db():
    engine, SessionLocal = create_session_factory()

    try:
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("DB_CONNECTIVITY_OK", extra={"result": result.scalar()})

            result = await session.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'payments'
                ORDER BY ordinal_position
                """)
            )

            columns = [row[0] for row in result.fetchall()]
            logger.info("PAYMENTS_TABLE_COLUMNS", extra={"columns": columns})

            return columns
    finally:
        await engine.dispose()
