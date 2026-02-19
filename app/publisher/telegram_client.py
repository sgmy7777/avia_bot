from __future__ import annotations

import httpx


class TelegramPublisher:
    def __init__(self, bot_token: str, channel: str) -> None:
        self._bot_token = bot_token
        self._channel = channel

    def publish(self, text: str) -> None:
        if not self._bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._channel,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
