import time
import requests
import os

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

NGROK_API = "http://ngrok:4040/api/tunnels"

def get_ngrok_url():
    for _ in range(30):
        try:
            r = requests.get(NGROK_API, timeout=2)
            tunnels = r.json()["tunnels"]
            for t in tunnels:
                if t["proto"] == "https":
                    return t["public_url"]
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("ngrok tunnel not found")

public_url = get_ngrok_url()

webhook_url = f"{public_url}/telegram/webhook"

resp = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={"url": webhook_url},
)

print("Webhook URL:", webhook_url)
print("Telegram response:", resp.text)
