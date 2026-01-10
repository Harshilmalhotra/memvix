# app/handlers/reminders.py

from app.models.reminder import Reminder
from app.services.scheduler import schedule_reminder
from app.services.telegram_client import send_message
from app.utils.time_format import format_datetime_for_user
from app.nlp.parser import parse_reminder_text


def handle_create_reminder(db, user, telegram_id, text):
    # ─────────────────────────────
    # 1️⃣ CHECK PENDING STATES (Conversation Flow)
    # ─────────────────────────────
    
    # Case A: User has pending time, provided message now
    if user.pending_trigger_time:
        # The input text IS the message
        return _create_reminder(db, user, telegram_id, text, user.pending_trigger_time)

    # Case B: User has pending message, provided time now
    if user.pending_reminder_message:
        # The input text SHOULD contain time
        # strict=False allows "10 pm" without "remind me"
        parsed_time = parse_reminder_text(text, user.timezone, strict=False)
        
        # If text is JUST time (e.g. "Tomorrow at 5pm"), parser might return intent="create_reminder_missing_message"
        # because it stripped the time and found no message. PRECISELY WHAT WE WANT.
        if parsed_time and parsed_time["trigger_time"]:
             return _create_reminder(db, user, telegram_id, user.pending_reminder_message, parsed_time["trigger_time"])
        
        # If users says "Actually remind me to buy milk tomorrow", we might restart flow?
        # For now, let's try to extract time from whatever they said.
        
        send_message(telegram_id, "⏰ I still need the time. When should I remind you?")
        return True


    # ─────────────────────────────
    # 2️⃣ NEW REMINDER (NLP)
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

    # 🔶 Case: Missing Message -> Ask "What?"
    if parsed["intent"] == "create_reminder_missing_message":
        user.pending_trigger_time = parsed["trigger_time"]
        user.pending_reminder_message = None # Clear other state
        db.add(user)
        db.commit()
        db.refresh(user)

        formatted_time = format_datetime_for_user(parsed["trigger_time"], user.timezone)
        send_message(
            telegram_id,
            f"⏰ Got it for *{formatted_time}*.\n\nWhat should I remind you about?"
        )
        return True

    # 🔶 Case: Missing Time -> Ask "When?"
    if parsed["intent"] == "create_reminder_missing_time":
        user.pending_reminder_message = parsed["message"]
        user.pending_trigger_time = None # Clear other state
        db.add(user)
        db.commit()
        db.refresh(user)

        send_message(
            telegram_id,
            f"📝 Reminder: *{parsed['message']}*\n\nWhen should I remind you?"
        )
        return True

    # ✅ Fully valid reminder
    if parsed["intent"] == "create_reminder":
        return _create_reminder(db, user, telegram_id, parsed["message"], parsed["trigger_time"])

    return True


def _create_reminder(db, user, telegram_id, message, trigger_time):
    # Clear valid states
    user.pending_trigger_time = None
    user.pending_reminder_message = None
    db.add(user)
    
    reminder = Reminder(
        user_id=user.id,
        telegram_id=telegram_id,
        message=message.strip(),
        trigger_time=trigger_time,
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
        chat_id=telegram_id,
        text=(
            "✅ *Okay! Reminder set*\n\n"
            f"🆔 *ID:* `{reminder.public_id}`\n"
            f"🗓 *When:* {formatted_time}\n"
            f"📝 *What:* {reminder.message}"
        ),
        reply_markup=keyboard,
    )

    return True
