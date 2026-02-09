from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.future import select 
from app.shared.models import Payment 
async def check_idempotency( 
        session: AsyncSession, 
        idempotency_key: str 
        ): 
        result = await session.execute( 
                select(Payment).where(Payment.idempotency_key == idempotency_key) 
                ) 
        return result.scalar_one_or_none() 
