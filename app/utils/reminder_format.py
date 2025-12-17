from zoneinfo import ZoneInfo

def format_reminder_line(reminder, user_timezone):
    local_time = reminder.trigger_time.astimezone(
        ZoneInfo(user_timezone)
    )

    return (
        f"• `{reminder.public_id}` — "
        f"{local_time.strftime('%d %b %I:%M %p')} — "
        f"{reminder.message}"
    )
