import requests
import os

from dotenv import load_dotenv

load_dotenv()  # 🔥 REQUIRED

BOT_TOKEN = os.getenv("BOT_TOKEN")
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
   