#app/services/telegram_client.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # 🔥 REQUIRED

DEPLOYMENT = os.getenv("DEPLOYMENT")

if DEPLOYMENT == "local":
    BOT_TOKEN = os.getenv("LOCAL_BOT_TOKEN")
elif DEPLOYMENT == "PROD":
    BOT_TOKEN = os.getenv("PROD_BOT_TOKEN")
else:
    raise RuntimeError("Invalid DEPLOYMENT value. Must be 'local' or 'PROD'.")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set for current DEPLOYMENT")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id: int, text: str, reply_markup: dict | None = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json=payload,
        timeout=5
    )
    response.raise_for_status()


def answer_callback_query(callback_query_id: str, text: str | None = None):
    payload = {
        "callback_query_id": callback_query_id
    }
    if text:
        payload["text"] = text

    requests.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json=payload,
        timeout=5
    )
