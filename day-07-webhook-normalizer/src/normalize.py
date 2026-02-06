from __future__ import annotations

from typing import Any, Dict, Optional
import uuid


# Known sources we explicitly support
KNOWN_SOURCES = {"stripe", "github"}


def detect_source(headers: Dict[str, str]) -> str:
    """
    Determine the event source from headers.

    Priority:
    1. Explicit X-Event-Source header
    2. Known vendor-specific headers
    3. Fallback to 'unknown'
    """
    source = headers.get("x-event-source")
    if source:
        return source

    # Vendor-specific detection (explicit, not heuristic)
    if "x-github-event" in headers:
        return "github"

    return "unknown"


def extract_event_id(
    source: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
) -> str:
    """
    Extract a stable event identifier.

    Falls back to a generated UUID if no source-specific
    identifier is available.
    """
    # Source-specific IDs
    if source == "stripe":
        event_id = payload.get("id")
        if isinstance(event_id, str):
            return event_id

    if source == "github":
        delivery_id = headers.get("x-github-delivery")
        if delivery_id:
            return delivery_id

    # Explicit override
    explicit_id = headers.get("x-event-id")
    if explicit_id:
        return explicit_id

    # Last resort: generated UUID
    return str(uuid.uuid4())


def extract_event_type(
    source: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
) -> str:
    """
    Extract a descriptive event type.

    This is best-effort and intentionally conservative.
    """
    if source == "stripe":
        event_type = payload.get("type")
        if isinstance(event_type, str):
            return event_type

    if source == "github":
        gh_event = headers.get("x-github-event")
        if gh_event:
            return gh_event

    return "unknown"


def normalize_payload(
    source: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce a conservative, source-aware normalized payload.

    Unknown sources always return an empty object.
    """
    if source == "stripe":
        return _normalize_stripe(payload)

    if source == "github":
        return _normalize_github(payload)

    return {}


def _normalize_stripe(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a Stripe webhook payload.

    Only extracts fields with stable, well-understood semantics.
    """
    data = payload.get("data", {})
    obj = data.get("object", {})

    normalized: Dict[str, Any] = {}

    if isinstance(obj.get("id"), str):
        normalized["object_id"] = obj["id"]

    if isinstance(obj.get("customer"), str):
        normalized["customer_id"] = obj["customer"]

    if isinstance(obj.get("amount_due"), int):
        normalized["amount_due"] = obj["amount_due"]

    if isinstance(obj.get("currency"), str):
        normalized["currency"] = obj["currency"]

    if isinstance(obj.get("status"), str):
        normalized["status"] = obj["status"]

    return normalized


def _normalize_github(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a GitHub webhook payload.

    Extracts shallow, high-signal fields only.
    """
    normalized: Dict[str, Any] = {}

    repo = payload.get("repository", {})
    if isinstance(repo, dict):
        full_name = repo.get("full_name")
        if isinstance(full_name, str):
            normalized["repository"] = full_name

    sender = payload.get("sender", {})
    if isinstance(sender, dict):
        login = sender.get("login")
        if isinstance(login, str):
            normalized["actor"] = login

    return normalized
