from __future__ import annotations

import logging

import httpx

from app.ai.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from app.domain.models import Incident

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def rewrite_incident(self, incident: Incident) -> str:
        if not self._api_key:
            return self._fallback(incident)

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(incident)},
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=40.0) as client:
                response = client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeepSeek unavailable, using fallback rewrite: %s", exc)
            return self._fallback(incident)

    def _fallback(self, incident: Incident) -> str:
        return (
            f"✈️ **{incident.aircraft} — {incident.location}**\n\n"
            f"🚨 **Зафиксирован авиационный инцидент.**\n\n"
            f"⚠️ *Дата:* {incident.date_utc}. *Локация:* {incident.location}. "
            f"*Судно:* {incident.aircraft}. *Сводка:* {incident.summary}.\n\n"
            f"Источник: {incident.source_url}\n\n"
            "#авиация #происшествие #авиабезопасность"
        )
