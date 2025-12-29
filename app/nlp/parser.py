from datetime import datetime, timezone
import re
import dateparser
from zoneinfo import ZoneInfo


def parse_reminder_text(text: str, user_timezone: str):
    if not text or not user_timezone:
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
    # ─────────────────────────────
    if " to " in cleaned:
        time_part, message_part = cleaned.split(" to ", 1)
    else:
        match = re.match(r"(.+?)\s+(call|do|buy|send|make)\s+(.+)", cleaned)
        if not match:
            parsed_dt = _safe_parse_datetime(cleaned, user_timezone)
            if not parsed_dt:
                return None

            return {
                "intent": "create_reminder_missing_message",
                "trigger_time": parsed_dt,
            }

        time_part = match.group(1)
        message_part = f"{match.group(2)} {match.group(3)}"

    # ─────────────────────────────
    # Parse datetime (SAFE)
    # ─────────────────────────────
    parsed_dt = _safe_parse_datetime(time_part, user_timezone)
    if not parsed_dt:
        return None

    return {
        "intent": "create_reminder",
        "trigger_time": parsed_dt,
        "message": message_part.strip(),
    }


# ─────────────────────────────
# Helpers
# ─────────────────────────────
def _safe_parse_datetime(text: str, user_timezone: str):
    """
    Dateparser wrapper that NEVER crashes.
    """
    tz = ZoneInfo(user_timezone)
    now = datetime.now(tz)

    settings = {
        "TIMEZONE": user_timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }

    # ✅ Only include RELATIVE_BASE if valid
    if now:
        settings["RELATIVE_BASE"] = now

    parsed = dateparser.parse(text, settings=settings)
    if not parsed:
        return None

    return parsed.astimezone(timezone.utc)


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
