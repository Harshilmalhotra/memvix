from app.models.user import User
from app.services.telegram_client import send_message

COUNTRY_TIMEZONES = {
    "india": ["Asia/Kolkata"],
    "uk": ["Europe/London"],
    "united kingdom": ["Europe/London"],
    "japan": ["Asia/Tokyo"],
    "china": ["Asia/Shanghai"],
    "singapore": ["Asia/Singapore"],
    "germany": ["Europe/Berlin"],
    "france": ["Europe/Paris"],
    "italy": ["Europe/Rome"],
    "uae": ["Asia/Dubai"],
}

MULTI_TZ_COUNTRIES = {
    "usa": [
        ("Eastern", "America/New_York"),
        ("Central", "America/Chicago"),
        ("Mountain", "America/Denver"),
        ("Pacific", "America/Los_Angeles"),
    ],
    "united states": [
        ("Eastern", "America/New_York"),
        ("Central", "America/Chicago"),
        ("Mountain", "America/Denver"),
        ("Pacific", "America/Los_Angeles"),
    ],
}


def handle_onboarding(db, telegram_id, first_name, username, text):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    # ───────────────
    # New user
    # ───────────────
    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            country=None,
            timezone=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        send_message(
            telegram_id,
            f"👋 Hi {first_name}!\n\n"
            "I’m *Memvix* — your personal reminder assistant.\n\n"
            "🌍 Which country are you in?\n"
            "_Example: India, USA, UK_\n\n"
            "📍 Or tap the button below to share your location.",
            reply_markup={
                "keyboard": [
                    [
                        {
                            "text": "📍 Share my location",
                            "request_location": True
                        }
                    ]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
        )

        return None, True  # 🔒 stop flow

    # ───────────────
    # Country not set
    # ───────────────
    if user.country is None:
        return _handle_country_input(db, user, telegram_id, text)

    # ───────────────
    # Timezone not set (multi-TZ case)
    # ───────────────
    if user.timezone is None:
        _send_timezone_choices(telegram_id, user.country)
        return None, True  # 🔒 stop flow

    return user, False  # onboarding complete


def _handle_country_input(db, user, chat_id, text):
    country = text.lower().strip()

    # Single-timezone country
    if country in COUNTRY_TIMEZONES:
        user.country = country
        user.timezone = COUNTRY_TIMEZONES[country][0]
        db.commit()

        send_message(
            chat_id,
            f"✅ Country set to *{country.title()}*\n"
            f"🕒 Timezone: *{user.timezone}*\n\n"
            "You can now create reminders 🎉"
        )
        return None, True

    # Multi-timezone country
    if country in MULTI_TZ_COUNTRIES:
        user.country = country
        db.commit()
        _send_timezone_choices(chat_id, country)
        return None, True

    # Unknown country
    send_message(
        chat_id,
        "❌ I couldn’t recognize that country.\n"
        "Please type a country name like *India*, *USA*, *UK*."
    )
    return None, True


def _send_timezone_choices(chat_id, country):
    zones = MULTI_TZ_COUNTRIES.get(country, [])

    reply_markup = {
        "inline_keyboard": [
            [{"text": label, "callback_data": f"tz:{tz}"}]
            for label, tz in zones
        ]
    }

    send_message(
        chat_id,
        f"🌍 You’re in *{country.title()}*.\n"
        "Which region are you in?",
        reply_markup=reply_markup
    )
