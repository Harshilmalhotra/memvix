import time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
import app.models
from app.services.telegram_client import send_message

from app.services.scheduler import fetch_due_reminders, remove_reminder

def run_worker():
    print("🔔 Reminder worker started")

    while True:
        due_ids = fetch_due_reminders()
        print("⏱️ Due IDs:", due_ids)

        if not due_ids:
            time.sleep(1)
            continue

        db: Session = SessionLocal()

        try:
            for reminder_id in due_ids:
                reminder = db.query(app.models.Reminder).get(int(reminder_id))
                if reminder and reminder.status == "scheduled":
                    send_message(
                        chat_id=reminder.telegram_id,
                        text=f"⏰ Reminder:\n{reminder.message}"
                    )

                    reminder.status = "sent"
                    db.commit()

                    print(f"📨 Sent reminder: {reminder.message}")
                    remove_reminder(reminder_id)


        finally:
            db.close()

if __name__ == "__main__":
    run_worker()
