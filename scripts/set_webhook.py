import time
import requests
import os
from dotenv import load_dotenv
load_dotenv()
DEPLOYMENT = os.getenv("DEPLOYMENT")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set for current DEPLOYMENT.")

NGROK_API = os.getenv("NGROK_API")
if not NGROK_API:
    raise RuntimeError("NGROK_API not set for current DEPLOYMENT.")


def get_ngrok_url():
    for _ in range(30):
        try:
            r = requests.get(
                NGROK_API,
                headers={"Accept": "application/json"},
                timeout=2,
            )
            data = r.json()
            for t in data.get("tunnels", []):
                if t.get("proto") == "https":
                    return t.get("public_url")
        except Exception as e:
            print("Waiting for ngrok...", e)
        time.sleep(2)

    raise RuntimeError("ngrok tunnel not found")


public_url = get_ngrok_url()
webhook_url = f"{public_url}/telegram/webhook"

resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={"url": webhook_url},
)

print("DEPLOYMENT:", DEPLOYMENT)
print("Webhook set to:", webhook_url)
print("Telegram response:", resp.text)
