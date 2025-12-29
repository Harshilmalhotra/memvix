# app/handlers/callbacks.py

from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.reminder import Reminder
from app.services.scheduler import remove_reminder
from app.services.telegram_client import (
    send_message,
    answer_callback_query
)


def handle_callback(callback: dict, db: Session):
    """
    Single source of truth for ALL Telegram callbacks.
    """

    data = callback.get("data")
    chat_id = callback["message"]["chat"]["id"]
    callback_id = callback["id"]

    # Always ACK if data is missing
    if not data or ":" not in data:
        answer_callback_query(callback_id)
        return

    # ─────────────────────────────
    # 1️⃣ Timezone selection (ONBOARDING)
    # ─────────────────────────────
    if data.startswith("tz:"):
        timezone = data.split("tz:", 1)[1]

        try:
            ZoneInfo(timezone)  # validate
        except Exception:
            answer_callback_query(callback_id, "Invalid timezone")
            send_message(chat_id, "❌ Invalid timezone selection.")
            return

        user = db.query(User).filter(User.telegram_id == chat_id).first()
        if not user:
            answer_callback_query(callback_id, "User not found")
            return

        user.timezone = timezone
        db.commit()

        send_message(
            chat_id,
            f"✅ Timezone set to *{timezone}*.\n\n"
            "You can now create reminders 🎉\n"
            "_Example: Remind me tomorrow at 7 PM to call mom_"
        )

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
            Reminder.status == "scheduled"
        )
        .first()
    )

    if not reminder:
        answer_callback_query(callback_id, "Not found")
        return

    if action == "cancel":
        reminder.status = "cancelled"
        db.commit()
        remove_reminder(reminder.id)

        send_message(chat_id, f"❌ Reminder `{public_id}` cancelled.")
        answer_callback_query(callback_id, "Cancelled")

    elif action == "edit":
        send_message(
            chat_id,
            f"✏️ Send new text for reminder `{public_id}`"
        )
        answer_callback_query(callback_id, "Edit mode")

    else:
        answer_callback_query(callback_id)
