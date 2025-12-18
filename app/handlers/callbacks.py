from sqlalchemy.orm import Session
from app.models.reminder import Reminder
from app.services.scheduler import remove_reminder
from app.services.telegram_client import send_message, answer_callback_query


def handle_callback(callback: dict, db: Session):
    data = callback.get("data")
    chat_id = callback["message"]["chat"]["id"]
    callback_id = callback["id"]

    if not data or ":" not in data:
        answer_callback_query(callback_id)
        return

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
