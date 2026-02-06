import uuid
from fastapi import FastAPI, Request
from mangum import Mangum

from app.api.routes import payments, notifications
from app.workers.payment_worker import process_payment
from app.workers.notification_worker import process_notification
from app.services.analytics_job import run_daily_analytics
from app.core.logging import logger

# ==========================================================
# FastAPI app (MUST be created FIRST)
# ==========================================================
app = FastAPI(title="Event Driven Platform")

# ==========================================================
# Lambda adapter (wrap AFTER app creation)
# ==========================================================
handler = Mangum(app)

# ==========================================================
# Middleware: Correlation / Request ID
# ==========================================================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "REQUEST_RECEIVED",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )
    return response

# ==========================================================
# Routers (PUBLIC)
# ==========================================================
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# ==========================================================
# Health Check (used by ALB / API Gateway)
# ==========================================================
@app.get("/health")
async def health():
    return {"status": "ok"}

# ==========================================================
# Startup hook (SAFE for Lambda)
# ==========================================================
@app.on_event("startup")
async def startup():
    logger.info("APPLICATION_STARTUP")

# ==========================================================
# INTERNAL ENDPOINTS (LOCAL DEV / TEST ONLY)
# In AWS these are replaced by SQS / EventBridge triggers
# ==========================================================
@app.post("/internal/process-payment/{payment_id}")
async def trigger_payment_worker(payment_id: str):
    await process_payment(payment_id)
    return {"status": "payment processing triggered"}

@app.post("/internal/process-notification/{event_type}")
async def trigger_notification_worker(event_type: str, payload: dict):
    await process_notification(event_type, payload)
    return {"status": "notification triggered"}

@app.post("/internal/run-analytics")
async def trigger_analytics_job():
    await run_daily_analytics()
    return {"status": "analytics completed"}
