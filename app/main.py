from fastapi import FastAPI
from app.api.routes import payments, notifications

app = FastAPI(title="Event Driven Platform")

app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/health")
async def health():
    return {"status": "ok"}
