from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.reminder import Reminder
from app.services.scheduler import (
    remove_reminder,
    schedule_reminder,
)
from app.services.telegram_client import (
    send_message,
    answer_callback_query,
    edit_message_reply_markup,  # 🔥 NEW
)


def handle_callback(callback: dict, db: Session):
    data = callback.get("data")
    message = callback.get("message")
    callback_id = callback["id"]

    if not message:
        answer_callback_query(callback_id)
        return

    chat_id = message["chat"]["id"]
    message_id = message["message_id"]  # 🔥 IMPORTANT

    if not data or ":" not in data:
        answer_callback_query(callback_id)
        return

    # ─────────────────────────────
    # 1️⃣ Timezone selection
    # ─────────────────────────────
    if data.startswith("tz:"):
        timezone_str = data.split("tz:", 1)[1]

        try:
            ZoneInfo(timezone_str)
        except Exception:
            answer_callback_query(callback_id, "Invalid timezone")
            return

        user = db.query(User).filter(User.telegram_id == chat_id).first()
        if not user:
            answer_callback_query(callback_id, "User not found")
            return

        user.timezone = timezone_str
        db.commit()

        send_message(chat_id, f"✅ Timezone set to *{timezone_str}*")
        answer_callback_query(callback_id, "Timezone set")
        return

    # ─────────────────────────────
    # 2️⃣ Reminder actions
    # ─────────────────────────────
    action, public_id = data.split(":", 1)

    reminder = (
        db.query(Reminder)
        .filter(
            Reminder.public_id == public_id,
            Reminder.telegram_id == chat_id,
        )
        .first()
    )

    if not reminder:
        answer_callback_query(callback_id, "Reminder not found")
        return

    # ❌ Cancel
    if action == "cancel":
        reminder.status = "cancelled"
        db.commit()
        remove_reminder(reminder.id)

        # 🔥 REMOVE KEYBOARD
        edit_message_reply_markup(chat_id, message_id, None)

        send_message(chat_id, "❌ Reminder cancelled.")
        answer_callback_query(callback_id, "Cancelled")
        return

    # ✏️ Edit
    if action == "edit":
        edit_message_reply_markup(chat_id, message_id, None)  # 🔥
        send_message(chat_id, f"✏️ Send new text for reminder `{public_id}`")
        answer_callback_query(callback_id, "Edit mode")
        return

    # ✅ Done
    if action == "done":
        reminder.status = "done"
        db.commit()
        remove_reminder(reminder.id)

        edit_message_reply_markup(chat_id, message_id, None)  # 🔥

        send_message(chat_id, f"✅ *Marked done*\n\n{reminder.message}")
        answer_callback_query(callback_id, "Done")
        return

    # ⏰ Snooze
    if action.startswith("snooze"):
        minutes = 10 if action == "snooze10" else 60
        new_trigger_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        reminder.trigger_time = new_trigger_time
        reminder.status = "scheduled"
        db.commit()

        remove_reminder(reminder.id)
        schedule_reminder(reminder.id, new_trigger_time)

        edit_message_reply_markup(chat_id, message_id, None)  # 🔥

        user_tz = ZoneInfo(reminder.timezone or "UTC")
        local_time = new_trigger_time.astimezone(user_tz)

        send_message(
            chat_id,
            f"⏰ Snoozed for *{minutes} minutes*\n"
            f"Next reminder at *{local_time.strftime('%I:%M %p')}*",
        )

        answer_callback_query(callback_id, "Snoozed")
        return

    answer_callback_query(callback_id)
