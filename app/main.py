from fastapi import FastAPI
from app.api.telegram import router as telegram_router

app = FastAPI(title="RemindZ")

app.include_router(telegram_router)

@app.get("/health")
def health():
    return {"status": "ok"}
