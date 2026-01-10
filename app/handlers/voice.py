# app/handlers/voice.py

import requests
import tempfile
import os

from app.core.config import settings
from app.services.telegram_client import send_message
from app.handlers.reminders import handle_create_reminder
from app.nlp.speech_to_text import transcribe_audio


def handle_voice_message(db, user, telegram_id: int, voice: dict):
    """
    Handles Telegram voice messages:
    1. Downloads voice file from Telegram
    2. Transcribes using Deepgram
    3. Passes text into existing reminder flow
    """
    print("🗣️Deepgram key loaded:", bool(settings.DEEPGRAM_API_KEY))

    file_id = voice.get("file_id")
    if not file_id:
        send_message(telegram_id, "❌ Invalid voice message.")
        return

    try:
        # 1️⃣ Get file path from Telegram
        file_path = _get_telegram_file_path(file_id)

        # 2️⃣ Download audio to temp file
        audio_path = _download_voice_file(file_path)

        send_message(telegram_id, "🎙️ Processing your voice reminder...")

        # 3️⃣ Speech → Text (Deepgram)
        text = transcribe_audio(audio_path)

        # Cleanup temp file
        try:
            os.remove(audio_path)
        except OSError:
            pass

        if not text:
            send_message(
                telegram_id,
                "❌ I couldn’t understand the voice message.\n"
                "Please try again or send text.",
            )
            return

        # 4️⃣ Reuse existing reminder logic (IMPORTANT)
        handle_create_reminder(db, user, telegram_id, text)

    except Exception as e:
        # NEVER crash webhook
        print("Voice handler error:", e)
        send_message(
            telegram_id, "⚠️ Something went wrong while processing your voice message."
        )


# ─────────────────────────────
# Telegram helpers
# ─────────────────────────────


def _get_telegram_file_path(file_id: str) -> str:
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}" f"/getFile"

    resp = requests.get(url, params={"file_id": file_id}, timeout=10)
    resp.raise_for_status()

    return resp.json()["result"]["file_path"]


def _download_voice_file(file_path: str) -> str:
    url = (
        f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/"
        f"{file_path}"
    )

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    tmp.write(resp.content)
    tmp.close()

    return tmp.name
