from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone


def _parse_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_csv(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    items = [part.strip() for part in raw.split(",")]
    return [item for item in items if item]


def _default_asn_feed_urls() -> str:
    year = datetime.now(timezone.utc).year
    return (
        "https://aviation-safety.net/rss.xml,"
        f"https://aviation-safety.net/asndb/year/{year},"
        "https://aviation-safety.net/database/,"
        "https://aviation-safety.net/wikibase/dblist.php?Country="
    )


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_channel: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    database_url: str
    poll_interval_minutes: int
    user_agent: str
    dry_run: bool
    asn_feed_urls: list[str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_channel=os.getenv("TELEGRAM_CHANNEL", "@avia_crash"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data.db"),
            poll_interval_minutes=int(os.getenv("POLL_INTERVAL_MINUTES", "10")),
            user_agent=os.getenv(
                "USER_AGENT",
                "avia-bot/1.0 (+https://github.com/example/avia_bot)",
            ),
            dry_run=_parse_bool("DRY_RUN", False),
            asn_feed_urls=_parse_csv("ASN_FEED_URLS", _default_asn_feed_urls()),
        )
