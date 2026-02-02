import pytest

from src.validation import validate_invoice_data, ValidationError


def valid_invoice_data():
    return {
        "invoice_number": "INV-001",
        "invoice_date": "2026-02-03",
        "company": {
            "name": "Acme Ltd",
            "address": "123 Queen Street",
            "email": "billing@acme.co.nz",
        },
        "client": {
            "name": "Bronson Pieper",
            "address": "456 King Street",
            "email": "bronson@example.com",
        },
        "line_items": [
            {
                "description": "Consulting work",
                "quantity": 5,
                "unit_price": 100.0,
            }
        ],
        "tax_rate": 0.15,
    }


def test_valid_invoice_passes_validation():
    validate_invoice_data(valid_invoice_data())


def test_missing_required_field_raises_error():
    data = valid_invoice_data()
    del data["client"]

    with pytest.raises(ValidationError):
        validate_invoice_data(data)


def test_empty_line_items_raises_error():
    data = valid_invoice_data()
    data["line_items"] = []

    with pytest.raises(ValidationError):
        validate_invoice_data(data)


def test_negative_quantity_raises_error():
    data = valid_invoice_data()
    data["line_items"][0]["quantity"] = -1

    with pytest.raises(ValidationError):
        validate_invoice_data(data)


def test_invalid_tax_rate_raises_error():
    data = valid_invoice_data()
    data["tax_rate"] = 1.5

    with pytest.raises(ValidationError):
        validate_invoice_data(data)
