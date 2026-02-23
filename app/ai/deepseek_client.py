from __future__ import annotations

import logging

import httpx

from app.ai.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from app.domain.models import Incident

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._disabled_reason = ""

    def rewrite_incident(self, incident: Incident) -> str:
        if not self._api_key:
            return self._fallback(incident)

        if self._disabled_reason:
            logger.info("DeepSeek disabled for current run (%s), using fallback.", self._disabled_reason)
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

        endpoint = f"{self._base_url}/chat/completions"

        try:
            with httpx.Client(timeout=40.0) as client:
                response = client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as exc:
            details = self._extract_error_details(exc.response)
            if exc.response.status_code == 402:
                self._disabled_reason = "deepseek_402_payment_required"
                logger.warning(
                    "DeepSeek 402 Payment Required. Отключаем запросы к DeepSeek до перезапуска. details=%s",
                    details,
                )
            else:
                logger.warning("DeepSeek API error, using fallback rewrite: %s", details)
            return self._fallback(incident)
        except Exception as exc:  # noqa: BLE001
            logger.warning("DeepSeek unavailable, using fallback rewrite: %s", exc)
            return self._fallback(incident)

    @staticmethod
    def _extract_error_details(response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                if "error" in data:
                    return str(data["error"])
                if "message" in data:
                    return str(data["message"])
                if "detail" in data:
                    return str(data["detail"])
                if "description" in data:
                    return str(data["description"])
        except Exception:  # noqa: BLE001
            pass
        return response.text.strip() or f"status={response.status_code}"

    def _fallback(self, incident: Incident) -> str:
        aircraft = incident.aircraft or "Воздушное судно"
        location = incident.location or "уточняется"
        date = incident.date_utc or "дата уточняется"
        operator = incident.operator or "оператор уточняется"
        onboard = incident.persons_onboard or "данные уточняются"

        return (
            f"✈️ **{aircraft} — инцидент в районе {location}**\n\n"
            f"📍 **Подробности:** {date} воздушное судно {aircraft} "
            f"({operator}) выполняло полет в районе {location}. "
            f"По предварительной информации, экипаж сообщил о нештатной ситуации, "
            f"после чего полет был прерван и борт выполнил вынужденное завершение полета. "
            f"Оперативные службы отработали по стандартному протоколу.\n\n"
            f"На борту находились: {onboard}. Информация о пострадавших и степени повреждений "
            f"уточняется официальными службами. Начата проверка обстоятельств инцидента.\n\n"
            f"Источник: {incident.source_url}\n\n"
            "#авиация #происшествие #авиабезопасность #небонаграни"
        )
