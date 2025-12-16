from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.core.deps import get_db
from app.models.user import User
from app.models.reminder import Reminder
from app.services.scheduler import schedule_reminder
from app.nlp.parser import parse_reminder_text


router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook")
def telegram_webhook(payload: dict, db: Session = Depends(get_db)):
    message = payload.get("message")
    if not message:
        return {"ok": True}

    from_user = message.get("from")
    if not from_user:
        return {"ok": True}

    telegram_id = from_user["id"]
    first_name = from_user.get("first_name")
    username = from_user.get("username")

    text = message.get("text")
    if not text:
        return {"ok": True}

    # Fetch or create user
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username
        )
        db.add(user)
        db.commit()
        db.refresh(user)

  
    parsed = parse_reminder_text(text, user.timezone)

    if not parsed:
        return {"ok": True}

    reminder = Reminder(
        user_id=user.id,
        telegram_id=telegram_id,
        message=parsed["message"],
        trigger_time=parsed["trigger_time"]
    )

    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    schedule_reminder(reminder.id, reminder.trigger_time)

    return {"ok": True}
