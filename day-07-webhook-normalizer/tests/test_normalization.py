from src.normalize import (
    detect_source,
    extract_event_id,
    extract_event_type,
    normalize_payload,
)
from src.schema import CanonicalEvent


def test_detect_github_source_from_header():
    headers = {"x-github-event": "push"}
    assert detect_source(headers) == "github"


def test_detect_unknown_source_by_default():
    assert detect_source({}) == "unknown"


def test_stripe_event_id_extraction():
    payload = {"id": "evt_123"}
    event_id = extract_event_id(
        source="stripe",
        payload=payload,
        headers={},
    )
    assert event_id == "evt_123"


def test_github_event_id_from_delivery_header():
    headers = {"x-github-delivery": "abc-123"}
    event_id = extract_event_id(
        source="github",
        payload={},
        headers=headers,
    )
    assert event_id == "abc-123"


def test_fallback_event_id_is_generated():
    event_id = extract_event_id(
        source="unknown",
        payload={},
        headers={},
    )
    assert isinstance(event_id, str)
    assert len(event_id) > 0


def test_stripe_event_type_extraction():
    payload = {"type": "charge.succeeded"}
    event_type = extract_event_type(
        source="stripe",
        payload=payload,
        headers={},
    )
    assert event_type == "charge.succeeded"


def test_github_event_type_from_header():
    headers = {"x-github-event": "issues"}
    event_type = extract_event_type(
        source="github",
        payload={},
        headers=headers,
    )
    assert event_type == "issues"


def test_unknown_event_type_fallback():
    event_type = extract_event_type(
        source="unknown",
        payload={},
        headers={},
    )
    assert event_type == "unknown"


def test_stripe_payload_normalization_is_conservative():
    payload = {
        "data": {
            "object": {
                "id": "pi_123",
                "customer": "cus_456",
                "amount_due": 5000,
                "currency": "usd",
                "status": "paid",
                "extra_field": "ignored",
            }
        }
    }

    normalized = normalize_payload("stripe", payload)

    assert normalized == {
        "object_id": "pi_123",
        "customer_id": "cus_456",
        "amount_due": 5000,
        "currency": "usd",
        "status": "paid",
    }


def test_github_payload_normalization_is_shallow():
    payload = {
        "repository": {"full_name": "octocat/hello-world"},
        "sender": {"login": "octocat"},
        "action": "opened",
    }

    normalized = normalize_payload("github", payload)

    assert normalized == {
        "repository": "octocat/hello-world",
        "actor": "octocat",
    }


def test_canonical_event_serialization_roundtrip():
    event = CanonicalEvent(
        event_id="evt_1",
        source="test",
        event_type="example",
        received_at=CanonicalEvent.now_utc_iso(),
        raw_payload={"a": 1},
        normalized={"b": 2},
    )

    as_dict = event.to_dict()
    assert as_dict["event_id"] == "evt_1"
    assert as_dict["raw_payload"]["a"] == 1
