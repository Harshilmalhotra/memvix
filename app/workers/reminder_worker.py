import time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
import app.models

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
                if not reminder or reminder.status != "scheduled":
                    remove_reminder(reminder_id)
                    continue

                reminder.status = "sent"
                db.commit()

                print(f"🔔 Reminder fired: {reminder.message}")

                remove_reminder(reminder_id)

        finally:
            db.close()


# 🔥 THIS WAS MISSING
if __name__ == "__main__":
    run_worker()
