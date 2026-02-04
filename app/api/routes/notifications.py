from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def notifications_health():
    return {"status": "notifications service alive"}
