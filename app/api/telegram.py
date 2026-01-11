# app/api/telegram.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.user import User
from sqlalchemy.sql import func
from app.handlers.callbacks import handle_callback
from app.handlers.commands import handle_command
from app.handlers.onboarding import handle_onboarding
from app.handlers.reminders import handle_create_reminder
from app.handlers.location import handle_location 
from app.handlers.voice import handle_voice_message


router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
def telegram_webhook(payload: dict, db: Session = Depends(get_db)):
    
    # Extract telegram_id from message or callback
    telegram_id = None
    if payload.get("message"):
        telegram_id = payload["message"]["from"]["id"]
    elif payload.get("callback_query"):
        telegram_id = payload["callback_query"]["from"]["id"]

    # Update last_seen if we have an ID
    if telegram_id:
        db.query(User).filter(User.telegram_id == telegram_id).update(
            {"last_seen": func.now()}
        )
        db.commit()

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
    # VOICE MESSAGE (🎙️ MUST COME BEFORE TEXT)
    # ─────────────────────────────
    if message.get("voice"):
        user, _ = handle_onboarding(db, telegram_id, first_name, username, None)
        handle_voice_message(db, user, telegram_id, message["voice"])
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
    user, handled = handle_onboarding(db, telegram_id, first_name, username, text)
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
