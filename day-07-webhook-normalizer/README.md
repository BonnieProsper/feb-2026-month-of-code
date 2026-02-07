# Webhook Event Normalizer & Audit Log

A production-style internal tool for ingesting external webhook events,
normalizing them into a canonical schema, and recording an immutable audit log.

This is not a webhook platform.
This is a diagnostic ingestion layer designed for traceability, safety, and debuggability.

---

## Why this exists

Modern systems consume events from many third-party services (Stripe, GitHub, Slack, etc.).
Each source uses different payload shapes, identifiers, and semantics.

Without normalization:

- Downstream systems must handle every vendor’s quirks
- Debugging requires tribal knowledge
- Auditing and replay are unreliable
- Schema drift leaks across the system

This tool introduces a single internal event contract while preserving the original payload verbatim.

---

## What this tool does

- Accepts arbitrary JSON webhook payloads via HTTP
- Detects event source conservatively using explicit signals
- Extracts stable event identifiers where possible
- Normalizes high-signal fields into a canonical schema
- Writes events to an append-only SQLite audit log
- Enforces idempotency by `event_id`
- Provides a CLI for inspecting stored events

---

## What this tool intentionally does NOT do

- No retries
- No async workers
- No queues
- No authentication or signature enforcement
- No UI
- No mutation or auto-healing

This is infrastructure plumbing, not a product.

---

## Canonical Event Schema

Each ingested event is stored as:

```json
{
  "event_id": "string",
  "source": "stripe | github | unknown",
  "event_type": "string",
  "received_at": "ISO-8601 UTC timestamp",
  "raw_payload": { ... },
  "normalized": { ... }
}
```

Design principles:
- raw_payload is immutable and preserved verbatim
- normalized is source-aware but conservative
- Unknown or unstable fields are never inferred

## Running the server
Install dependencies:
```bash
pip install -r requirements.txt
```
Start the server:
```bash
uvicorn src.app:app --reload
```

## Sending a webhook

Example GitHub-style payload:
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: delivery-123" \
  -d '{"repository":{"full_name":"octocat/hello-world"},"sender":{"login":"octocat"}}'
```
## Inspecting stored events

The application exposes a CLI for read-only inspection:
```bash
python -m src.app inspect
python -m src.app inspect --source github
python -m src.app inspect --event-type push
python -m src.app inspect --normalized
python -m src.app inspect --raw
```

Flags:
- --source
- --event-type
- --limit
- --raw
- --normalized

---

## Storage & Idempotency

- Events are stored in SQLite
- Storage is append-only
- event_id is unique
- Duplicate deliveries return the original event
- No updates or deletes are allowed

This guarantees auditability and safe replays.

## Failure modes considered
- Duplicate webhook delivery
- Missing or partial metadata
- Unknown event sources
- Schema drift from third-party providers

Failures are surfaced explicitly and never silently corrected.

## Project structure
```text
src/
  app.py        # HTTP ingestion
  normalize.py  # Source-aware normalization logic
  schema.py     # Canonical schema definition
  storage.py    # Append-only audit log + CLI
tests/
  test_normalization.py
```