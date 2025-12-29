from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

def get_day_range(user_timezone: str, days_offset: int = 0):
    tz = ZoneInfo(user_timezone or "UTC")
    now = datetime.now(tz)

    start = (now + timedelta(days=days_offset)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(days=1)

    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)
