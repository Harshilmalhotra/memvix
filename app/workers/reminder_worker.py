import time
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.reminder import Reminder
from app.services.telegram_client import send_message
from app.services.scheduler import fetch_due_reminders, remove_reminder

POLL_INTERVAL = 5  # seconds


def run_worker():
    print("🔔 Reminder worker started")

    while True:
        due_ids = fetch_due_reminders()
        print("⏱️ Due IDs:", due_ids)

        if not due_ids:
            time.sleep(POLL_INTERVAL)
            continue

        db: Session = SessionLocal()

        try:
            for reminder_id in due_ids:
                try:
                    reminder = db.get(Reminder, int(reminder_id))

                    # Skip invalid / already handled reminders
                    if not reminder or reminder.status != "scheduled":
                        remove_reminder(reminder_id)
                        continue

                    user_tz = ZoneInfo(reminder.timezone or "UTC")
                    local_time = reminder.trigger_time.astimezone(user_tz)

                    keyboard = {
                        "inline_keyboard": [
                            [
                                {
                                    "text": "✅ Done",
                                    "callback_data": f"done:{reminder.public_id}",
                                },
                                {
                                    "text": "⏰ Snooze 10m",
                                    "callback_data": f"snooze10:{reminder.public_id}",
                                },
                                {
                                    "text": "⏰ Snooze 1h",
                                    "callback_data": f"snooze60:{reminder.public_id}",
                                },
                            ]
                        ]
                    }

                    send_message(
                        chat_id=reminder.telegram_id,
                        text=(
                            f"Reminder ({local_time.strftime('%I:%M %p')})\n\n"
                            f"{reminder.message}"
                        ),
                        reply_markup=keyboard,
                        parse_mode=None,  
                    )

                    # Mark as delivered
                    reminder.status = "delivered"
                    db.commit()

                    # Remove from Redis after delivery
                    remove_reminder(reminder_id)

                    print(f"📨 Delivered reminder {reminder.id}")

                except Exception as e:
                    print(f"❌ Failed reminder {reminder_id}: {e}")
                    db.rollback()

        finally:
            db.close()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_worker()
