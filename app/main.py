import uuid
from fastapi import FastAPI, Request
from mangum import Mangum
from sqlalchemy import text

from app.api.routes import payments, notifications
from app.core.logging import logger
from app.db.session import engine
from app.db.models import Base

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
# 🔥 CRITICAL FIX: disable slash redirect for API Gateway
app = FastAPI(
    title="Event Driven Platform",
    redirect_slashes=False,
)

print("🔥🔥 API IMAGE VERSION: 2026-02-07-FINAL-SLASH-FIX 🔥🔥")

# --------------------------------------------------
# Middleware: Request ID
# --------------------------------------------------
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

# --------------------------------------------------
# Routes
# --------------------------------------------------
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# --------------------------------------------------
# Health
# --------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# --------------------------------------------------
# Startup (SAFE for Lambda)
# --------------------------------------------------
@app.on_event("startup")
async def startup():
    logger.info("APPLICATION_STARTUP")

    async with engine.begin() as conn:
        # ✅ force DB connection check
        await conn.execute(text("SELECT 1"))

        # ✅ safe for Lambda (no migrations)
        await conn.run_sync(Base.metadata.create_all)

# --------------------------------------------------
# Lambda adapter (MUST be last)
# --------------------------------------------------
handler = Mangum(app)
