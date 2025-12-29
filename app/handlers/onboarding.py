from zoneinfo import ZoneInfo
from app.models.user import User
from app.services.telegram_client import send_message

def handle_onboarding(db, telegram_id, first_name, username, text):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            timezone=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        send_message(
            telegram_id,
            f"👋 Hi {first_name}!\n\n"
            "I’m *RemindZ* — your personal reminder assistant.\n\n"
            "Before we start, what timezone are you in?\n"
            "_Example: Asia/Kolkata_"
        )
        return None, True

    if user.timezone is None:
        try:
            ZoneInfo(text)
            user.timezone = text
            db.commit()

            send_message(
                telegram_id,
                f"✅ Timezone set to *{text}*.\n\n"
                "You can now create reminders.\n"
                "_Example: Remind me tomorrow at 7 PM to call mom_"
            )
        except Exception:
            send_message(
                telegram_id,
                "❌ Invalid timezone.\n"
                "Please send something like `Asia/Kolkata`."
            )
        return None, True

    return user, False
