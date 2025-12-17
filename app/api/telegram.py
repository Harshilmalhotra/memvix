from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.core.deps import get_db
from app.models.user import User
from app.models.reminder import Reminder
from app.services.scheduler import schedule_reminder
from app.services.telegram_client import send_message
from app.nlp.parser import parse_reminder_text
from app.utils.time_format import format_datetime_for_user, format_reminder_line


router = APIRouter(prefix="/telegram", tags=["Telegram"])


def get_day_range(user_timezone: str, days_offset: int = 0):
    tz = ZoneInfo(user_timezone or "UTC")
    now = datetime.now(tz)
    start = (now + timedelta(days=days_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


@router.post("/webhook")
def telegram_webhook(payload: dict, db: Session = Depends(get_db)):
    # -----------------------------
    # CALLBACK QUERY HANDLING
    # -----------------------------
    callback = payload.get("callback_query")
    if callback:
        data = callback.get("data")
        chat_id = callback["message"]["chat"]["id"]

        if not data or ":" not in data:
            return {"ok": True}

        action, public_id = data.split(":", 1)

        reminder = (
            db.query(Reminder)
            .filter(
                Reminder.public_id == public_id,
                Reminder.telegram_id == chat_id,
                Reminder.status == "scheduled"
            )
            .first()
        )

        if not reminder:
            send_message(chat_id, "⚠️ Reminder not found or already handled.")
            return {"ok": True}

        if action == "cancel":
            reminder.status = "cancelled"
            db.commit()
            send_message(chat_id, f"❌ Reminder `{public_id}` cancelled.")

        return {"ok": True}

    # -----------------------------
    # MESSAGE HANDLING
    # -----------------------------
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
            username=username,
            timezone="Asia/Kolkata"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # -----------------------------
    # COMMANDS
    # -----------------------------
    if text.startswith("/list"):
        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.telegram_id == telegram_id,
                Reminder.status == "scheduled"
            )
            .order_by(Reminder.trigger_time)
            .limit(10)
            .all()
        )

        if not reminders:
            send_message(telegram_id, "📭 No upcoming reminders.")
            return {"ok": True}

        lines = [format_reminder_line(r, user.timezone) for r in reminders]
        send_message(
            telegram_id,
            "*📋 Your upcoming reminders:*\n\n" + "\n".join(lines)
        )
        return {"ok": True}

    if text in ("/today", "/tomorrow"):
        offset = 0 if text == "/today" else 1
        start, end = get_day_range(user.timezone, offset)

        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.telegram_id == telegram_id,
                Reminder.status == "scheduled",
                Reminder.trigger_time >= start,
                Reminder.trigger_time < end
            )
            .order_by(Reminder.trigger_time)
            .all()
        )

        if not reminders:
            send_message(telegram_id, "📭 No reminders.")
            return {"ok": True}

        lines = [format_reminder_line(r, user.timezone) for r in reminders]
        send_message(
            telegram_id,
            f"*📅 Reminders for {text[1:]}:*\n\n" + "\n".join(lines)
        )
        return {"ok": True}

    # -----------------------------
    # NLP REMINDER PARSING
    # -----------------------------
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

    formatted_time = format_datetime_for_user(
        reminder.trigger_time,
        user.timezone
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "❌ Cancel", "callback_data": f"cancel:{reminder.public_id}"},
                {"text": "✏️ Edit", "callback_data": f"edit:{reminder.public_id}"}
            ]
        ]
    }

    confirmation_text = (
        "✅ *Okay! Reminder set*\n\n"
        f"🆔 *ID:* `{reminder.public_id}`\n"
        f"🗓 *When:* {formatted_time}\n"
        f"📝 *What:* {reminder.message}"
    )

    send_message(
        chat_id=telegram_id,
        text=confirmation_text,
        reply_markup=keyboard
    )

    return {"ok": True}
