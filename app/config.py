from __future__ import annotations

import os
from dataclasses import dataclass


def _parse_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_channel: str
    deepseek_api_key: str
    deepseek_model: str
    database_url: str
    poll_interval_minutes: int
    user_agent: str
    dry_run: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_channel=os.getenv("TELEGRAM_CHANNEL", "@avia_crash"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data.db"),
            poll_interval_minutes=int(os.getenv("POLL_INTERVAL_MINUTES", "10")),
            user_agent=os.getenv(
                "USER_AGENT",
                "avia-bot/1.0 (+https://github.com/example/avia_bot)",
            ),
            dry_run=_parse_bool("DRY_RUN", False),
        )
