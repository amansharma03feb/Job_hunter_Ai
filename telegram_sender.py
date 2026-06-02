import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)   # ensure .env is loaded before reading tokens


def send_message(text: str):
    """Send a message to the configured Telegram chat."""
    # Read fresh each call so env changes / late dotenv loads work
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID", "959971760")

    if not bot_token:
        print("[Telegram] TELEGRAM_BOT_TOKEN not set — skipping")
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN"}

    url     = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        resp = requests.post(url, data=payload, timeout=10)
        try:
            return resp.json()
        except Exception:
            return {"ok": False, "error": "Non-JSON response", "status": resp.status_code}
    except Exception as e:
        print(f"[Telegram] Send error: {e}")
        return {"ok": False, "error": str(e)}
