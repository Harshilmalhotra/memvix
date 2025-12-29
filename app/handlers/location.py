# app/handlers/location.py

from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

from app.models.user import User
from app.services.telegram_client import send_message

tf = TimezoneFinder()


def handle_location(db, telegram_id: int, location: dict):
    lat = location["latitude"]
    lon = location["longitude"]

    timezone = tf.timezone_at(lat=lat, lng=lon)

    if not timezone:
        send_message(
            telegram_id,
            "❌ Could not detect timezone from location.\n"
            "Please use /changetimezone."
        )
        return

    # Validate timezone
    ZoneInfo(timezone)

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return

    user.timezone = timezone
    user.country = "auto"
    db.commit()

    send_message(
        telegram_id,
        f"📍 Location detected!\n"
        f"🕒 Timezone set to *{timezone}*\n\n"
        "You can now create reminders 🎉",
        reply_markup={"remove_keyboard": True}
    )
