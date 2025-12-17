from datetime import timezone
import dateparser


def parse_reminder_text(text: str, user_timezone: str):
    text = text.lower().strip()

    if not text.startswith("remind me"):
        return None

    cleaned = text.replace("remind me", "").strip()

    if " to " not in cleaned:
        return None

    time_part, message_part = cleaned.split(" to ", 1)

    parsed_dt = dateparser.parse(
        time_part,
        settings={
            "TIMEZONE": user_timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future"
        }
    )

    if not parsed_dt:
        return None

    # 🔥 ALWAYS CONVERT TO UTC
    trigger_time_utc = parsed_dt.astimezone(timezone.utc)

    return {
        "intent": "create_reminder",
        "trigger_time": trigger_time_utc,
        "message": message_part.strip()
    }
