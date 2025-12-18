from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.services.telegram_client import send_message
from app.utils.reminder_format import format_reminder_line



# -----------------------------
# Helpers
# -----------------------------
def get_day_range(user_timezone: str, days_offset: int = 0):
    tz = ZoneInfo(user_timezone or "UTC")
    now = datetime.now(tz)

    start = (now + timedelta(days=days_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=1)

    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


# -----------------------------
# Command Dispatcher
# -----------------------------
def handle_command(
    text: str,
    telegram_id: int,
    user,
    db: Session
) -> bool:
    """
    Returns True if command was handled,
    False otherwise.
    """

    if text.startswith("/list"):
        return handle_list(telegram_id, user, db)

    if text == "/today":
        return handle_day(telegram_id, user, db, days_offset=0)

    if text == "/tomorrow":
        return handle_day(telegram_id, user, db, days_offset=1)

    return False


# -----------------------------
# Commands
# -----------------------------
def handle_list(telegram_id: int, user, db: Session) -> bool:
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
        return True

    lines = [
        format_reminder_line(r, user.timezone)
        for r in reminders
    ]

    send_message(
        telegram_id,
        "*📋 Your upcoming reminders:*\n\n" + "\n".join(lines)
    )

    return True


def handle_day(
    telegram_id: int,
    user,
    db: Session,
    days_offset: int
) -> bool:
    start, end = get_day_range(user.timezone, days_offset)

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

    label = "today" if days_offset == 0 else "tomorrow"

    if not reminders:
        send_message(
            telegram_id,
            f"📭 No reminders for {label}."
        )
        return True

    lines = [
        format_reminder_line(r, user.timezone)
        for r in reminders
    ]

    send_message(
        telegram_id,
        f"*📅 Reminders for {label}:*\n\n" + "\n".join(lines)
    )

    return True
