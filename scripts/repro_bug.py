import sys
import os
sys.path.append(os.getcwd())

from app.nlp.parser import parse_reminder_text

# Mock Settings
timezone = "Asia/Kolkata"

def test(text, strict=True):
    print(f"Input: '{text}' (strict={strict})")
    result = parse_reminder_text(text, timezone, strict=strict)
    print(f"Result: {result}")
    
    # Try workaround
    workaround_text = "remind me " + text
    print(f"Workaround Input: '{workaround_text}'")
    result_workaround = parse_reminder_text(workaround_text, timezone)
    print(f"Workaround Result: {result_workaround}")
    print("-" * 20)

test("10 pm", strict=False)
test("tomorrow at 5", strict=False)
test("At 10 pm remind me to dance")
