from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
import dateparser

REMINDER_KEYWORDS = [
    "remind",
    "remember",
    "alert",
    "notify",
]


from dateparser.search import search_dates

def parse_reminder_text(text: str, user_timezone: str, strict: bool = True):
    if not text or not user_timezone:
        return None

    original = text
    text = text.lower().strip()

    # 1️⃣ Check intent (Skipped if strict=False)
    if strict:
        if not any(word in text for word in REMINDER_KEYWORDS):
            return None

    # 2️⃣ Extract datetime (Use search_dates to find embedded time)
    trigger_time, text_without_time = _extract_datetime(text, user_timezone)

    # 3️⃣ Extract message from the remaining text
    # If we stripped the time, the message is what's left (plus some cleanup)
    # If we didn't find time, we process the whole text
    message = _extract_message(text_without_time or text)

    # 4️⃣ Distinguish Missing Info
    # Case A: Time is missing -> Intent: missing_time
    if not trigger_time:
        return {
            "intent": "create_reminder_missing_time",
            "trigger_time": None,
            "message": message or original, # Keep original if message extraction failed
        }

    # Case B: Message is missing -> Intent: missing_message
    if not message:
        return {
            "intent": "create_reminder_missing_message",
            "trigger_time": trigger_time,
            "message": None
        }

    # Case C: All good
    return {
        "intent": "create_reminder",
        "trigger_time": trigger_time,
        "message": message,
    }


# ─────────────────────────────────────────────


def _extract_datetime(text: str, user_timezone: str):
    tz = ZoneInfo(user_timezone)
    now = datetime.now(tz)

    settings = {
        "TIMEZONE": user_timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "RELATIVE_BASE": now.replace(tzinfo=None), # Fix for dateparser/search_dates issue with aware base
        "PREFER_DATES_FROM": "future",
    }

    # Try search_dates first (handles mixed text)
    # Force English to avoid "me" -> "Wednesday" (in Italian/Spanish/etc?)
    found = search_dates(text, languages=['en'], settings=settings)
    
    if found:
        # Filter garbage matches
        valid_matches = []
        for match_str, date_obj in found:
            # Ignore short words without digits (e.g. "me", "at")
            if len(match_str) < 3 and not any(char.isdigit() for char in match_str):
                continue
            # Ignore common false positives
            if match_str.lower() in ["remind", "reminder", "call"]:
                continue
            valid_matches.append((match_str, date_obj))

        if valid_matches:
            # Take the first VALID match
            match_str, date_obj = valid_matches[0]
            utc_dt = date_obj.astimezone(timezone.utc)
            text_without_time = text.replace(match_str, "")
            return utc_dt, text_without_time

    # Fallback: Try strict parsing (handles "10 pm" better sometimes)
    parsed = dateparser.parse(text, languages=['en'], settings=settings)
    if parsed:
        return parsed.astimezone(timezone.utc), text.replace(text, "") # Consumed all

    return None, text


def _extract_message(text: str) -> str:
    text = text.strip()
    # 1. Remove introductory reminder phrases
    # Match start of string or proper boundaries
    text = re.sub(r"^(remind me|remind|remember to|alert me|please|kindly)\b", "", text, flags=re.IGNORECASE).strip()
    
    # 2. Remove "to", "at", "on" if it's at the start (floating prepositions)
    text = re.sub(r"^(to|at|on|in)\b", "", text, flags=re.IGNORECASE).strip()

    # 3. Remove time expressions systematically (if any remain)
    
    # Absolute times (at 5pm, at 10:00)
    text = re.sub(r"\bat\s+\d{1,2}(:\d{2})?\s*(am|pm)?\b", "", text, flags=re.IGNORECASE)
    
    # Relative days (today, tomorrow, next friday)
    text = re.sub(r"\b(today|tomorrow|tonight|morning|evening|night)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(next|on)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", "", text, flags=re.IGNORECASE)
    
    # Relative durations (in 5 mins, in a week)
    text = re.sub(r"\bin\s+(\d+|a|an)\s+(seconds?|minutes?|hours?|days?|weeks?|months?)\b", "", text, flags=re.IGNORECASE)

    # 4. Clean up
    text = re.sub(r"\s+", " ", text) # multiple spaces
    return text.strip(" .")
