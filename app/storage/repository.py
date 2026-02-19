from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.domain.models import Incident


class IncidentRepository:
    def __init__(self, database_url: str) -> None:
        if not database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// URLs are supported in MVP")
        self._db_path = Path(database_url.removeprefix("sqlite:///"))
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date_utc TEXT,
                    location TEXT,
                    aircraft TEXT,
                    source_url TEXT,
                    rewrite_text TEXT,
                    status TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    published_at TEXT
                )
                """
            )
            conn.commit()

    def exists(self, incident_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM incidents WHERE incident_id = ? LIMIT 1", (incident_id,)
            )
            return cur.fetchone() is not None

    def save_discovered(self, incident: Incident) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO incidents (
                    incident_id, title, date_utc, location, aircraft, source_url,
                    rewrite_text, status, first_seen_at, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.incident_id,
                    incident.title,
                    incident.date_utc,
                    incident.location,
                    incident.aircraft,
                    incident.source_url,
                    "",
                    "discovered",
                    datetime.now(timezone.utc).isoformat(),
                    None,
                ),
            )
            conn.commit()

    def mark_published(self, incident_id: str, rewrite_text: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE incidents
                SET rewrite_text = ?, status = ?, published_at = ?
                WHERE incident_id = ?
                """,
                (
                    rewrite_text,
                    "published",
                    datetime.now(timezone.utc).isoformat(),
                    incident_id,
                ),
            )
            conn.commit()

    def mark_failed(self, incident_id: str, rewrite_text: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE incidents SET rewrite_text = ?, status = ? WHERE incident_id = ?",
                (rewrite_text, "failed", incident_id),
            )
            conn.commit()
