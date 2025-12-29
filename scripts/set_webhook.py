import time
import requests
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
NGROK_API = "http://ngrok:4040/api/tunnels"

def get_ngrok_url():
    for _ in range(30):
        try:
            r = requests.get(
                NGROK_API,
                headers={"Accept": "application/json"},
                timeout=2,
            )
            data = r.json()
            for t in data["tunnels"]:
                if t["proto"] == "https":
                    return t["public_url"]
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

print("Webhook set to:", webhook_url)
print("Telegram response:", resp.text)
