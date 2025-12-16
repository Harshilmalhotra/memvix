from datetime import datetime, timezone
import dateparser
import re


def parse_reminder_text(text: str, user_timezone: str = "Asia/Kolkata"):
    """
    Parses text like:
    'remind me tomorrow at 7 pm to buy batteries'
    """

    text = text.lower().strip()

    # ---- 1. Intent detection (simple & reliable)
    if not text.startswith("remind me"):
        return None

    # ---- 2. Remove trigger words
    cleaned = text.replace("remind me", "").strip()

    # ---- 3. Split message from time using 'to'
    if " to " not in cleaned:
        return None

    time_part, message_part = cleaned.split(" to ", 1)

    # ---- 4. Parse datetime
    parsed_dt = dateparser.parse(
        time_part,
        settings={
            "TIMEZONE": user_timezone,
            "RETURN_AS_TIMEZONE_AWARE": True
        }
    )

    if not parsed_dt:
        return None

    # ---- 5. Convert to UTC
    trigger_time_utc = parsed_dt.astimezone(timezone.utc)

    return {
        "intent": "create_reminder",
        "trigger_time": trigger_time_utc,
        "message": message_part.strip()
    }
