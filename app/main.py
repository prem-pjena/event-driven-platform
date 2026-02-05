from fastapi import FastAPI

from app.api.routes import payments, notifications
from app.db.session import engine
from app.db.models import Base
from app.workers.payment_worker import process_payment

app = FastAPI(title="Event Driven Platform")

# ------------------------
# Routers
# ------------------------
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# ------------------------
# Health check
# ------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ------------------------
# TEMP: Auto-create tables on startup
# (Will be replaced by Alembic later)
# ------------------------
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ------------------------
# INTERNAL endpoint (Simulates SQS → Lambda)
# DO NOT expose publicly in real systems
# ------------------------
@app.post("/internal/process-payment/{payment_id}")
async def trigger_payment_worker(payment_id: str):
    await process_payment(payment_id)
    return {"status": "processing triggered"}
