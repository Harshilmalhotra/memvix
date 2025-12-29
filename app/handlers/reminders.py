# app/handlers/reminders.py

from app.models.reminder import Reminder
from app.services.scheduler import schedule_reminder
from app.services.telegram_client import send_message
from app.utils.time_format import format_datetime_for_user
from app.nlp.parser import parse_reminder_text


def handle_create_reminder(db, user, telegram_id, text):
    # ─────────────────────────────
    # 1️⃣ COMPLETE PENDING REMINDER
    # ─────────────────────────────
    if user.pending_trigger_time:
        reminder = Reminder(
            user_id=user.id,
            telegram_id=telegram_id,
            message=text.strip(),
            trigger_time=user.pending_trigger_time,
            timezone=user.timezone,
            status="scheduled"
        )

        user.pending_trigger_time = None  # 🔥 clear state

        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        schedule_reminder(reminder.id, reminder.trigger_time)

        formatted_time = format_datetime_for_user(
            reminder.trigger_time,
            user.timezone
        )

        send_message(
            telegram_id,
            (
                "✅ *Reminder set!*\n\n"
                f"🗓 *When:* {formatted_time}\n"
                f"📝 *What:* {reminder.message}"
            )
        )
        return True

    # ─────────────────────────────
    # 2️⃣ NORMAL NLP FLOW
    # ─────────────────────────────
    parsed = parse_reminder_text(text, user.timezone)

    # ❌ Not a reminder
    if not parsed:
        send_message(
            telegram_id,
            "🤔 I couldn’t understand that.\n\n"
            "Try something like:\n"
            "• Remind me in *30 seconds* to call mom\n"
            "• Remind me tomorrow at *7 PM* to submit assignment\n"
            "• Remind me on *Monday at 10 AM* to join meeting"
        )
        return True

    # ⚠️ Time present, message missing
    if parsed["intent"] == "create_reminder_missing_message":
        user.pending_trigger_time = parsed["trigger_time"]
        db.commit()

        send_message(
            telegram_id,
            "⏰ Got it!\n\n"
            "What should I remind you about?"
        )
        return True

    # ✅ Fully valid reminder
    if parsed["intent"] != "create_reminder":
        return True

    reminder = Reminder(
        user_id=user.id,
        telegram_id=telegram_id,
        message=parsed["message"],
        trigger_time=parsed["trigger_time"],
        timezone=user.timezone,
        status="scheduled"
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
