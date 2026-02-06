from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict
from datetime import datetime, timezone
import json


@dataclass(frozen=True)
class CanonicalEvent:
    """
    Canonical representation of an ingested webhook event.

    This is an immutable record that separates:
    - raw truth (raw_payload)
    - interpreted meaning (normalized)

    It is intentionally minimal and conservative.
    """

    event_id: str
    source: str
    event_type: str
    received_at: str
    raw_payload: Dict[str, Any]
    normalized: Dict[str, Any]

    @staticmethod
    def now_utc_iso() -> str:
        """
        Generate an ISO 8601 UTC timestamp suitable for received_at.
        """
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the canonical event to a plain dictionary.
        """
        return asdict(self)

    def to_json(self) -> str:
        """
        Serialize the canonical event to a JSON string.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "CanonicalEvent":
        """
        Reconstruct a CanonicalEvent from a storage row.

        Assumes JSON fields are stored as serialized strings.
        """
        return CanonicalEvent(
            event_id=row["event_id"],
            source=row["source"],
            event_type=row["event_type"],
            received_at=row["received_at"],
            raw_payload=json.loads(row["raw_payload"]),
            normalized=json.loads(row["normalized"]),
        )
