import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def send_message(text: str):
    """Send a message to the configured Telegram chat.

    Tries multiple API endpoints to work around ISP blocks on Telegram
    (common with Jio/Airtel in India).
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID", "959971760")

    if not bot_token:
        print("[Telegram] TELEGRAM_BOT_TOKEN not set — skipping")
        return {"ok": False, "error": "Missing TELEGRAM_BOT_TOKEN"}

    payload = {"chat_id": chat_id, "text": text}

    # Multiple endpoints — ISP may block some but not all
    base_urls = [
        f"https://api.telegram.org/bot{bot_token}",
    ]

    # Check .env for a custom proxy URL (user can set TG_PROXY_URL=https://your-worker.workers.dev)
    proxy_url = os.getenv("TG_PROXY_URL", "")
    if proxy_url:
        base_urls.insert(0, f"{proxy_url.rstrip('/')}/bot{bot_token}")

    for base in base_urls:
        url = f"{base}/sendMessage"
        for attempt in range(3):
            try:
                resp = requests.post(url, data=payload, timeout=20)
                try:
                    result = resp.json()
                    if result.get("ok"):
                        return result
                    print(f"[Telegram] API error: {result.get('description', 'unknown')}")
                    return result
                except Exception:
                    return {"ok": False, "error": "Non-JSON response", "status": resp.status_code}
            except Exception as e:
                print(f"[Telegram] Send error (attempt {attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(5)

    return {"ok": False, "error": "All attempts failed — ISP likely blocking Telegram"}
