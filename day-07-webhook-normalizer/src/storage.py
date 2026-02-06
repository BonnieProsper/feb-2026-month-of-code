from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Optional, Iterable

from .schema import CanonicalEvent


DEFAULT_DB_PATH = Path("events.db")


class EventStorage:
    """
    Append-only storage for canonical webhook events.

    This class enforces:
    - one row per logical event
    - idempotency via event_id
    - immutable records
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    raw_payload TEXT NOT NULL,
                    normalized TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_by_event_id(self, event_id: str) -> Optional[CanonicalEvent]:
        """
        Retrieve an event by its logical event_id.
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT event_id, source, event_type, received_at, raw_payload, normalized
                FROM events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()

            if row is None:
                return None

            return CanonicalEvent.from_row(dict(row))

    def insert(self, event: CanonicalEvent) -> CanonicalEvent:
        """
        Insert a new canonical event.

        If an event with the same event_id already exists,
        the existing event is returned (idempotent behavior).
        """
        existing = self.get_by_event_id(event.event_id)
        if existing is not None:
            return existing

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id,
                    source,
                    event_type,
                    received_at,
                    raw_payload,
                    normalized
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.source,
                    event.event_type,
                    event.received_at,
                    json.dumps(event.raw_payload, ensure_ascii=False),
                    json.dumps(event.normalized, ensure_ascii=False),
                ),
            )
            conn.commit()

        return event

    def list_events(
        self,
        *,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterable[CanonicalEvent]:
        """
        List stored events, optionally filtered.

        Results are ordered by received_at descending.
        """
        query = """
            SELECT event_id, source, event_type, received_at, raw_payload, normalized
            FROM events
        """
        conditions = []
        params = []

        if source:
            conditions.append("source = ?")
            params.append(source)

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY received_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        for row in rows:
            yield CanonicalEvent.from_row(dict(row))
