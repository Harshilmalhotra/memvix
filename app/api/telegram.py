# app/api/telegram.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.handlers.callbacks import handle_callback
from app.handlers.commands import handle_command
from app.handlers.onboarding import handle_onboarding
from app.handlers.reminders import handle_create_reminder
from app.handlers.location import handle_location  # 🔥 NEW

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
def telegram_webhook(payload: dict, db: Session = Depends(get_db)):

    # ─────────────────────────────
    # CALLBACKS (inline buttons)
    # ─────────────────────────────
    if payload.get("callback_query"):
        handle_callback(payload["callback_query"], db)
        return {"ok": True}

    # ─────────────────────────────
    # MESSAGE
    # ─────────────────────────────
    message = payload.get("message")
    if not message:
        return {"ok": True}

    from_user = message["from"]
    telegram_id = from_user["id"]
    first_name = from_user.get("first_name")
    username = from_user.get("username")

    # ─────────────────────────────
    # LOCATION (📍 auto timezone)
    # ─────────────────────────────
    if message.get("location"):
        handle_location(db, telegram_id, message["location"])
        return {"ok": True}

    # ─────────────────────────────
    # TEXT MESSAGE
    # ─────────────────────────────
    text = message.get("text")
    if not text:
        return {"ok": True}

    # ─────────────────────────────
    # ONBOARDING (country / timezone)
    # ─────────────────────────────
    user, handled = handle_onboarding(
        db, telegram_id, first_name, username, text
    )
    if handled:
        return {"ok": True}

    # ─────────────────────────────
    # COMMANDS
    # ─────────────────────────────
    if handle_command(text, telegram_id, user, db):
        return {"ok": True}

    # ─────────────────────────────
    # REMINDERS
    # ─────────────────────────────
    handle_create_reminder(db, user, telegram_id, text)
    return {"ok": True}
