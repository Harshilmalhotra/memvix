import time
from datetime import datetime, timezone
from app.core.redis import redis_client

REMINDER_ZSET = "scheduled_reminders"


def schedule_reminder(reminder_id: int, trigger_time: datetime):
    """
    Store reminder in Redis sorted set.
    Score = UNIX timestamp
    """
    timestamp = int(trigger_time.replace(tzinfo=timezone.utc).timestamp())
    redis_client.zadd(REMINDER_ZSET, {str(reminder_id): timestamp})


def fetch_due_reminders():
    """
    Fetch reminders that are due now or earlier
    """
    now = int(time.time())
    return redis_client.zrangebyscore(
        REMINDER_ZSET, min=0, max=now
    )


def remove_reminder(reminder_id: int):
    redis_client.zrem(REMINDER_ZSET, str(reminder_id))
