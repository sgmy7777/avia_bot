from __future__ import annotations

import argparse
import logging
import time

from app.ai.deepseek_client import DeepSeekClient
from app.ai.validator import validate_rewrite
from app.bootstrap import load_dotenv
from app.collector.aviation_safety import AviationSafetyCollector
from app.config import Settings
from app.domain.models import Incident
from app.domain.normalizer import normalize_incident
from app.publisher.telegram_client import TelegramPublisher
from app.storage.repository import IncidentRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("avia_bot")


def _merge_with_details(incident: Incident, details: dict[str, str]) -> Incident:
    if not details:
        return incident

    return Incident(
        incident_id=incident.incident_id,
        title=details.get("title") or incident.title,
        event_type=incident.event_type,
        date_utc=details.get("date_utc") or incident.date_utc,
        location=details.get("location") or incident.location,
        aircraft=details.get("aircraft") or incident.aircraft,
        operator=details.get("operator") or incident.operator,
        persons_onboard=incident.persons_onboard,
        summary=details.get("summary") or incident.summary,
        source_url=incident.source_url,
    )


def _build_rewriter(settings: Settings) -> DeepSeekClient:
    if settings.llm_provider == "openrouter":
        api_key = settings.openrouter_api_key
        model = settings.openrouter_model
        base_url = settings.openrouter_base_url
        extra_headers = {
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        }
        provider_name = "openrouter"
        if not api_key:
            logger.warning("LLM_PROVIDER=openrouter, но OPENROUTER_API_KEY пуст. Будет использован fallback-рерайт.")
    else:
        api_key = settings.deepseek_api_key
        model = settings.deepseek_model
        base_url = settings.deepseek_base_url
        extra_headers = {}
        provider_name = "deepseek"

    logger.info("LLM provider: %s | model: %s | base_url: %s", provider_name, model, base_url)

    return DeepSeekClient(
        api_key=api_key,
        model=model,
        base_url=base_url,
        provider_name=provider_name,
        extra_headers=extra_headers,
    )


def process_once(settings: Settings) -> None:
    collector = AviationSafetyCollector(settings.user_agent, settings.asn_feed_urls)
    repository = IncidentRepository(settings.database_url)
    rewriter = _build_rewriter(settings)
    publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_channel)

    raw_items = collector.fetch_recent_incidents()
    logger.info("fetched %d candidate incidents", len(raw_items))

    new_count = 0
    for raw in raw_items:
        incident = normalize_incident(raw)
        if repository.exists(incident.incident_id):
            continue

        details = collector.fetch_incident_details(incident.source_url)
        incident = _merge_with_details(incident, details)

        new_count += 1
        repository.save_discovered(incident)

        try:
            rewritten = rewriter.rewrite_incident(incident)
            valid, reason = validate_rewrite(rewritten)
            if not valid:
                logger.warning("rewrite validation failed for %s: %s", incident.incident_id, reason)

            if settings.dry_run:
                logger.info("DRY_RUN=true, skip publish for %s", incident.incident_id)
                repository.mark_skipped(incident.incident_id, "dry_run_skip_publish")
                continue

            publisher.publish(rewritten)
            repository.mark_published(incident.incident_id, rewritten)
            logger.info("published incident %s", incident.incident_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to process incident %s: %s", incident.incident_id, exc)
            repository.mark_failed(incident.incident_id, str(exc))

    logger.info("new incidents processed: %d", new_count)


def send_test_message(settings: Settings) -> None:
    publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_channel)
    text = (
        "✅ Тестовое сообщение avia_bot\n\n"
        "Интеграция Telegram настроена корректно."
    )
    publisher.publish(text)
    logger.info("test message sent to %s", settings.telegram_channel)


def run_forever(settings: Settings) -> None:
    logger.info("starting worker with interval=%s min", settings.poll_interval_minutes)
    while True:
        try:
            process_once(settings)
        except Exception as exc:  # noqa: BLE001
            logger.exception("worker cycle failed: %s", exc)
        time.sleep(settings.poll_interval_minutes * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASN -> Telegram monitoring bot")
    parser.add_argument("--once", action="store_true", help="process incidents once and exit")
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="send one test message to Telegram channel and exit",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    settings = Settings.from_env()

    if args.test_telegram:
        send_test_message(settings)
        return

    if args.once:
        try:
            process_once(settings)
        except Exception as exc:  # noqa: BLE001
            logger.error("one-shot run failed: %s", exc)
        return

    run_forever(settings)


if __name__ == "__main__":
    main()
