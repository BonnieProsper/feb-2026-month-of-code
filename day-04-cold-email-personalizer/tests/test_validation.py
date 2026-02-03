import pytest

from src.validation import validate_prospects, ValidationError


def test_valid_prospects_pass_validation():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
            "recent_event": "launched a new platform",
        }
    ]

    required_fields = {"first_name", "company", "recent_event"}

    validate_prospects(prospects, required_fields)


def test_missing_required_field_raises_error():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
        }
    ]

    required_fields = {"first_name", "company", "recent_event"}

    with pytest.raises(ValidationError) as exc:
        validate_prospects(prospects, required_fields)

    assert 'Missing required field "recent_event"' in str(exc.value)


def test_empty_value_is_treated_as_missing():
    prospects = [
        {
            "first_name": "Sam",
            "company": "Manning",
            "recent_event": "   ",
        }
    ]

    required_fields = {"recent_event"}

    with pytest.raises(ValidationError):
        validate_prospects(prospects, required_fields)


def test_error_message_includes_company_when_available():
    prospects = [
        {
            "company": "Manning",
            "recent_event": "",
        }
    ]

    required_fields = {"recent_event"}

    with pytest.raises(ValidationError) as exc:
        validate_prospects(prospects, required_fields)

    assert "company=Manning" in str(exc.value)
