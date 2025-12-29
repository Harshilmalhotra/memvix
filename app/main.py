from fastapi import FastAPI
from app.api.telegram import router as telegram_router

app = FastAPI(title="Memvix")


@app.on_event("startup")
def startup_event():
    import app.init_db  # creates tables if they don't exist


app.include_router(telegram_router)


@app.get("/health")
def health():
    return {"status": "ok"}
