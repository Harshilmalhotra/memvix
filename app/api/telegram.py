from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.handlers.callbacks import handle_callback
from app.handlers.commands import handle_command
from app.handlers.onboarding import handle_onboarding
from app.handlers.reminders import handle_create_reminder

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
def telegram_webhook(payload: dict, db: Session = Depends(get_db)):

    # CALLBACKS
    if payload.get("callback_query"):
        handle_callback(payload["callback_query"], db)
        return {"ok": True}

    message = payload.get("message")
    if not message or not message.get("text"):
        return {"ok": True}

    from_user = message["from"]
    telegram_id = from_user["id"]
    first_name = from_user.get("first_name")
    username = from_user.get("username")
    text = message["text"]

    # ONBOARDING
    user, handled = handle_onboarding(
        db, telegram_id, first_name, username, text
    )
    if handled:
        return {"ok": True}

    # COMMANDS
    if handle_command(text, telegram_id, user, db):
        return {"ok": True}

    # CREATE REMINDER
    handle_create_reminder(db, user, telegram_id, text)
    return {"ok": True}
