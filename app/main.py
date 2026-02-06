from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(title="Event Driven Platform")

handler = Mangum(app)

@app.get("/health")
async def health():
    return {"status": "ok"}
