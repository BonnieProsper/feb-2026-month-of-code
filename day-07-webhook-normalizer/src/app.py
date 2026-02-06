from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from .schema import CanonicalEvent
from .normalize import (
    detect_source,
    extract_event_id,
    extract_event_type,
    normalize_payload,
)
from .storage import EventStorage


app = FastAPI(title="Webhook Event Normalizer")

storage = EventStorage()


@app.post("/webhook")
async def ingest_webhook(request: Request) -> JSONResponse:
    """
    Ingest an arbitrary webhook payload, normalize it,
    and append it to the audit log.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON payload must be an object")

    # Normalize headers to lowercase for consistent access
    headers: Dict[str, str] = {
        k.lower(): v for k, v in request.headers.items()
    }

    source = detect_source(headers)
    event_id = extract_event_id(source, payload, headers)
    event_type = extract_event_type(source, payload, headers)

    normalized = normalize_payload(source, payload)

    event = CanonicalEvent(
        event_id=event_id,
        source=source,
        event_type=event_type,
        received_at=CanonicalEvent.now_utc_iso(),
        raw_payload=payload,
        normalized=normalized,
    )

    try:
        stored = storage.insert(event)
    except Exception:
        # Storage failures should surface clearly
        raise HTTPException(status_code=500, detail="Failed to persist event")

    return JSONResponse(content=stored.to_dict())


def _run_cli(argv: list[str]) -> None:
    """
    CLI entry point for inspecting stored events.
    """
    parser = argparse.ArgumentParser(
        description="Inspect stored webhook events"
    )
    subparsers = parser.add_subparsers(dest="command")

    inspect_parser = subparsers.add_parser(
        "inspect", help="List stored events"
    )
    inspect_parser.add_argument(
        "--source", help="Filter by event source"
    )
    inspect_parser.add_argument(
        "--event-type", help="Filter by event type"
    )
    inspect_parser.add_argument(
        "--limit", type=int, help="Limit number of results"
    )
    inspect_parser.add_argument(
        "--raw", action="store_true", help="Include raw payload"
    )
    inspect_parser.add_argument(
        "--normalized", action="store_true", help="Include normalized payload"
    )

    args = parser.parse_args(argv)

    if args.command != "inspect":
        parser.print_help()
        sys.exit(1)

    events = list(
        storage.list_events(
            source=args.source,
            event_type=args.event_type,
            limit=args.limit,
        )
    )

    if not events:
        print("No events found.")
        return

    for event in events:
        print(f"Event ID: {event.event_id}")
        print(f"Source: {event.source}")
        print(f"Type: {event.event_type}")
        print(f"Received At: {event.received_at}")

        if args.normalized:
            print("Normalized:")
            print(json.dumps(event.normalized, indent=2, ensure_ascii=False))

        if args.raw:
            print("Raw Payload:")
            print(json.dumps(event.raw_payload, indent=2, ensure_ascii=False))

        print("-" * 40)


if __name__ == "__main__":
    _run_cli(sys.argv[1:])
