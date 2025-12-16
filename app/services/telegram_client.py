import requests
import os

from dotenv import load_dotenv

load_dotenv()  # 🔥 REQUIRED

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id: int, text: str):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
