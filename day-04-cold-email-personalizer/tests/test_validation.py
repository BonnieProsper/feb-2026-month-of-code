# tests/test_validation.py

import pytest

from src.validation import validate_prospects
from src.errors import ValidationError


def test_valid_prospects_pass_validation():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
            "recent_event": "launched a new platform",
        }
    ]

    required_fields = {"first_name", "company", "recent_event"}

    # Should not raise
    validate_prospects(prospects, required_fields)


def test_missing_required_field_is_skipped():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
        }
    ]

    required_fields = {"first_name", "company", "recent_event"}

    result = validate_prospects(prospects, required_fields)

    assert len(result.valid_prospects) == 0
    assert len(result.skipped_prospects) == 1
    assert 'Missing required field "recent_event"' in result.skipped_prospects[0].reason


def test_empty_value_is_treated_as_missing():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
            "recent_event": "   ",
        }
    ]

    required_fields = {"recent_event"}

    result = validate_prospects(prospects, required_fields)

    assert len(result.valid_prospects) == 0
    assert len(result.skipped_prospects) == 1


def test_error_message_includes_company_when_available():
    prospects = [
        {
            "company": "Manning",
            "recent_event": "",
        }
    ]

    required_fields = {"recent_event"}

    result = validate_prospects(prospects, required_fields)

    assert len(result.skipped_prospects) == 1
    assert "company=Manning" in result.skipped_prospects[0].reason
