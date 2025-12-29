from app.models.reminder import Reminder
from app.services.scheduler import schedule_reminder
from app.services.telegram_client import send_message
from app.utils.time_format import format_datetime_for_user
from app.nlp.parser import parse_reminder_text

def handle_create_reminder(db, user, telegram_id, text):
    parsed = parse_reminder_text(text, user.timezone)
    if not parsed:
        send_message(
            telegram_id,
            "🤔 I couldn’t fully understand the time.\n"
            "Can you rephrase?"
        )
        return True

    reminder = Reminder(
        user_id=user.id,
        telegram_id=telegram_id,
        message=parsed["message"],
        trigger_time=parsed["trigger_time"],
        timezone=user.timezone
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
        "inline_keyboard": [[
            {"text": "❌ Cancel", "callback_data": f"cancel:{reminder.public_id}"},
            {"text": "✏️ Edit", "callback_data": f"edit:{reminder.public_id}"}
        ]]
    }

    send_message(
        telegram_id,
        (
            "✅ *Okay! Reminder set*\n\n"
            f"🆔 *ID:* `{reminder.public_id}`\n"
            f"🗓 *When:* {formatted_time}\n"
            f"📝 *What:* {reminder.message}"
        ),
        reply_markup=keyboard
    )

    return True
