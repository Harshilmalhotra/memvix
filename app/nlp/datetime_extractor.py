# app/nlp/datetime_extractor.py

import requests
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

DUCKLING_URL = "http://localhost:8001/parse"


FUZZY_DEFAULTS = {
    "tonight": 21,  # 9 PM
    "evening": 19,  # 7 PM
    "morning": 9,  # 9 AM
    "afternoon": 14,  # 2 PM
    "noon": 12,
    "midnight": 0,
}


def extract_datetime(text: str, user_timezone: str):
    response = requests.post(
        DUCKLING_URL,
        data={
            "text": text,
            "locale": "en_US",
            "timezone": user_timezone,
        },
        timeout=2,
    )

    response.raise_for_status()
    data = response.json()

    tz = ZoneInfo(user_timezone)

    for item in data:
        if item.get("dim") != "time":
            continue

        value = item["value"]

        # ✅ Case 1: Exact datetime provided
        if "value" in value:
            dt = datetime.fromisoformat(value["value"])

        # ✅ Case 2: Values list with concrete time
        elif "values" in value:
            first = value["values"][0]
            if "value" in first:
                dt = datetime.fromisoformat(first["value"])
            else:
                # ❗ FUZZY time like "tonight"
                dt = _resolve_fuzzy_time(text, tz)

        else:
            continue

        # Normalize to UTC
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=tz).astimezone(timezone.utc)

        return dt, item["start"], item["end"]

    return None, None, None


def _resolve_fuzzy_time(text: str, tz: ZoneInfo) -> datetime:
    now = datetime.now(tz)
    lowered = text.lower()

    for keyword, hour in FUZZY_DEFAULTS.items():
        if keyword in lowered:
            return datetime.combine(
                now.date(),
                time(hour=hour),
                tzinfo=tz,
            )

    # Safe fallback → 1 hour from now
    return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
