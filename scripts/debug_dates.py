import sys
import os
import datetime
from dateparser.search import search_dates

sys.path.append(os.getcwd())

from zoneinfo import ZoneInfo
timezone_str = "Asia/Kolkata"

def debug_search_dates(text):
    print(f"DEBUG search_dates('{text}')")
    tz = ZoneInfo(timezone_str)
    now = datetime.datetime.now(tz).replace(tzinfo=None) # Naive wall time
    settings = {
        "TIMEZONE": timezone_str,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": now
    }
    found = search_dates(text, languages=['en'], settings=settings)
    print(f"Found: {found}")
    print("-" * 20)

debug_search_dates("at 10 pm remind me to dance")
