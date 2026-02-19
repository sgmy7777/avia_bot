from __future__ import annotations

import logging
import time

from app.ai.deepseek_client import DeepSeekClient
from app.ai.validator import validate_rewrite
from app.collector.aviation_safety import AviationSafetyCollector
from app.config import Settings
from app.domain.normalizer import normalize_incident
from app.publisher.telegram_client import TelegramPublisher
from app.storage.repository import IncidentRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("avia_bot")


def process_once(settings: Settings) -> None:
    collector = AviationSafetyCollector(settings.user_agent)
    repository = IncidentRepository(settings.database_url)
    rewriter = DeepSeekClient(settings.deepseek_api_key, settings.deepseek_model)
    publisher = TelegramPublisher(settings.telegram_bot_token, settings.telegram_channel)

    raw_items = collector.fetch_recent_incidents()
    logger.info("fetched %d candidate incidents", len(raw_items))

    new_count = 0
    for raw in raw_items:
        incident = normalize_incident(raw)
        if repository.exists(incident.incident_id):
            continue

        new_count += 1
        repository.save_discovered(incident)

        try:
            rewritten = rewriter.rewrite_incident(incident)
            valid, reason = validate_rewrite(rewritten)
            if not valid:
                logger.warning("rewrite validation failed for %s: %s", incident.incident_id, reason)

            publisher.publish(rewritten)
            repository.mark_published(incident.incident_id, rewritten)
            logger.info("published incident %s", incident.incident_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed to process incident %s: %s", incident.incident_id, exc)
            repository.mark_failed(incident.incident_id, str(exc))

    logger.info("new incidents processed: %d", new_count)


def run_forever() -> None:
    settings = Settings.from_env()
    logger.info("starting worker with interval=%s min", settings.poll_interval_minutes)
    while True:
        process_once(settings)
        time.sleep(settings.poll_interval_minutes * 60)


if __name__ == "__main__":
    run_forever()
