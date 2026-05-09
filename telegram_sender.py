import os
import requests

# Read bot token from environment for safety. If you prefer another env var name,
# set TELEGRAM_BOT_TOKEN in your environment before running.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
# Chat id can also be provided via env var TELEGRAM_CHAT_ID as fallback.
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "959971760")


def send_message(text: str):
    """Send a message to the configured Telegram chat using BOT_TOKEN.

    Returns a dict with the Telegram API response, or an error dict when the
    token is missing or the request fails.
    """

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN environment variable"}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        # If Telegram returns non-JSON (rare), fall back to text
        try:
            return response.json()
        except Exception:
            return {"ok": False, "error": "Invalid JSON response from Telegram", "status_code": response.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}
