from app.nlp.datetime_extractor import extract_datetime


def parse_reminder_text(text: str, user_timezone: str):
    if not text or not user_timezone:
        return None

    lowered = text.lower().strip()

    # 1️⃣ Intent gate (strict + predictable)
    if not lowered.startswith("remind me"):
        return None

    content = text[len("remind me") :].strip()

    # 2️⃣ Extract datetime via Duckling
    trigger_time, start, end = extract_datetime(content, user_timezone)
    if not trigger_time:
        return None

    # 3️⃣ Remove time span safely
    message = (content[:start] + content[end:]).strip()

    # Normalize message
    message = message.lstrip("to ").strip()
    print(f"Extracted message: '{message}'")
    # 4️⃣ Slot filling decision
    if not message:
        return {
            "intent": "create_reminder_missing_message",
            "trigger_time": trigger_time,
        }

    return {
        "intent": "create_reminder",
        "trigger_time": trigger_time,
        "message": message,
    }
