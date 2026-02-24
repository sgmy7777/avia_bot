from __future__ import annotations

import httpx


class TelegramPublisher:
    def __init__(self, bot_token: str, channel: str) -> None:
        self._bot_token = bot_token
        self._channel = channel

    def publish(self, text: str) -> None:
        if not self._bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")
        if not self._channel:
            raise RuntimeError("TELEGRAM_CHANNEL is empty")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._channel,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, json=payload)
            if response.is_success:
                return

            details = self._extract_telegram_error(response)
            if response.status_code == 400 and "can't parse entities" in details.lower():
                fallback_payload = {
                    "chat_id": self._channel,
                    "text": text,
                    "disable_web_page_preview": True,
                }
                fallback_response = client.post(url, json=fallback_payload)
                if fallback_response.is_success:
                    return
                response = fallback_response
                details = self._extract_telegram_error(response)

        raise RuntimeError(
            "Telegram sendMessage failed. "
            f"status={response.status_code}; chat_id={self._channel}; details={details}"
        )

    @staticmethod
    def _extract_telegram_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            description = data.get("description")
            if description:
                return str(description)
        except Exception:  # noqa: BLE001
            pass

        text = response.text.strip()
        if text:
            return text
        return "unknown error"
