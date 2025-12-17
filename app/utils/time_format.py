from datetime import datetime
from zoneinfo import ZoneInfo


def format_datetime_for_user(dt_utc: datetime, user_timezone: str) -> str:
    local_dt = dt_utc.astimezone(ZoneInfo(user_timezone))

    return local_dt.strftime("%A, %d %b at %I:%M %p")
