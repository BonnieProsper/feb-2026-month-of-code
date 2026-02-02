from src.invoice_generator import generate_invoice


def base_invoice_data():
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


def test_line_total_calculation():
    invoice = generate_invoice(base_invoice_data())
    assert invoice["line_items"][0]["line_total"] == 500.0


def test_subtotal_calculation():
    invoice = generate_invoice(base_invoice_data())
    assert invoice["subtotal"] == 500.0


def test_tax_calculation():
    invoice = generate_invoice(base_invoice_data())
    assert invoice["tax_amount"] == 75.0


def test_total_calculation():
    invoice = generate_invoice(base_invoice_data())
    assert invoice["total"] == 575.0
