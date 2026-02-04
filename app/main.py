from fastapi import FastAPI

from app.api.routes import payments, notifications
from app.db.session import engine
from app.db.models import Base

app = FastAPI(title="Event Driven Platform")

# Routers
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# TEMP: Auto-create tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
