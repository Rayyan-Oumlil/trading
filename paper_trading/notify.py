"""Telegram alerts. Missing credentials are an error, never a silent skip."""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set")
    body = json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"Telegram HTTP {response.status}")


if __name__ == "__main__":
    send_telegram(" ".join(sys.argv[1:]))
