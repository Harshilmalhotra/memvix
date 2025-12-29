from datetime import timezone
import re
import dateparser


def parse_reminder_text(text: str, user_timezone: str):
    if not text:
        return None

    text = text.lower().strip()

    # Must start with "remind me"
    if not text.startswith("remind me"):
        return None

    cleaned = text.replace("remind me", "", 1).strip()

    # ─────────────────────────────
    # Normalize common human mistakes
    # ─────────────────────────────
    cleaned = _normalize_time_units(cleaned)

    # ─────────────────────────────
    # Split time and message
    # Prefer "to", fallback to last space
    # ─────────────────────────────
    if " to " in cleaned:
        time_part, message_part = cleaned.split(" to ", 1)
    else:
        # fallback: try splitting last word group
        match = re.match(r"(.+?)\s+(call|do|buy|send|make)\s+(.+)", cleaned)
        if not match:
            parsed_dt = dateparser.parse(
                cleaned,
                settings={
                    "TIMEZONE": user_timezone,
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "PREFER_DATES_FROM": "future"
                }
            )

            if not parsed_dt:
                return None

            return {
                "intent": "create_reminder_missing_message",
                "trigger_time": parsed_dt.astimezone(timezone.utc)
            }


        time_part = match.group(1)
        message_part = match.group(2) + " " + match.group(3)

    # ─────────────────────────────
    # Parse datetime
    # ─────────────────────────────
    parsed_dt = dateparser.parse(
        time_part,
        settings={
            "TIMEZONE": user_timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": None
        }
    )

    if not parsed_dt:
        return None

    # Convert to UTC
    trigger_time_utc = parsed_dt.astimezone(timezone.utc)

    return {
        "intent": "create_reminder",
        "trigger_time": trigger_time_utc,
        "message": message_part.strip()
    }


def _normalize_time_units(text: str) -> str:
    """
    Makes dateparser tolerant to human input.
    """
    replacements = {
        r"\bsecond\b": "seconds",
        r"\bminute\b": "minutes",
        r"\bhour\b": "hours",
        r"\bday\b": "days",
        r"\bweek\b": "weeks",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text
