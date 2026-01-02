# app/services/telegram_client.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ─────────────────────────────
# MarkdownV2 escape (CORRECT)
# ─────────────────────────────
def escape_markdown_v2(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return "".join(f"\\{c}" if c in escape_chars else c for c in text)


def send_message(
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
    *,
    parse_mode: str | None = "Markdown",
    escape: bool = False,
):
    if escape and parse_mode == "MarkdownV2":
        text = escape_markdown_v2(text)

    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json=payload,
        timeout=10,
    )

    if not response.ok:
        print("Telegram send_message failed:", response.text)


def answer_callback_query(callback_query_id: str, text: str | None = None):
    payload = {"callback_query_id": callback_query_id}

    if text:
        payload["text"] = text

    response = requests.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json=payload,
        timeout=10,
    )

    if not response.ok:
        print("Telegram answerCallbackQuery failed:", response.text)


def edit_message_reply_markup(
    chat_id: int,
    message_id: int,
    reply_markup: dict | None,
):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": reply_markup,
    }

    response = requests.post(
        f"{TELEGRAM_API}/editMessageReplyMarkup",
        json=payload,
        timeout=10,
    )

    if not response.ok:
        print("Telegram editMessageReplyMarkup failed:", response.text)
