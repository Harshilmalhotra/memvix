from deepgram import DeepgramClient
from app.core.config import settings
import os

# Deepgram client reads DEEPGRAM_API_KEY from env
deepgram = DeepgramClient()


def transcribe_audio(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as audio_file:
            response = deepgram.listen.v1.media.transcribe_file(
                request=audio_file.read(),
                model="nova-3",
                smart_format=True,
                language="en",
            )

        transcript = response.results.channels[0].alternatives[0].transcript

        return transcript.strip() if transcript else None

    except Exception as e:
        print("Deepgram transcription failed:", e)
        return None
