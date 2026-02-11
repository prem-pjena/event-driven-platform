import uuid
from fastapi import FastAPI, Request
from mangum import Mangum

from app.api.routes import payments, notifications
from app.core.logging import logger

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(
    title="Event Driven Platform",
    redirect_slashes=False,
)

logger.info("🔥🔥 API IMAGE VERSION: 2026-02-11-FINAL-API-CLEAN 🔥🔥")

# --------------------------------------------------
# Middleware: Request ID + structured logging
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
            "status_code": response.status_code,
        },
    )

    return response


# --------------------------------------------------
# Routes
# --------------------------------------------------
app.include_router(
    payments.router,
    prefix="/payments",
    tags=["payments"],
)

app.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
)

# --------------------------------------------------
# Health (ALB / Lambda safe)
# --------------------------------------------------
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


# --------------------------------------------------
# Startup (NO DB, NO NETWORK)
# --------------------------------------------------
@app.on_event("startup")
async def startup():
    logger.info("APPLICATION_STARTUP_COMPLETE")


# --------------------------------------------------
# Lambda adapter (MUST be last)
# --------------------------------------------------
handler = Mangum(app
    app,
    api_gateway_base_path=None,

)
