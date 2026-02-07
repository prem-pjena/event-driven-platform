from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.logging import logger

async def probe_db():
    async with AsyncSessionLocal() as session:
        # Basic connectivity
        result = await session.execute(text("SELECT 1"))
        logger.info("DB_CONNECTIVITY_OK", extra={"result": result.scalar()})

        # Table existence
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
