import os
import tempfile

from src.invoice_generator import generate_invoice
from src.pdf_utils import generate_invoice_pdf


def sample_invoice():
    return {
        "invoice_number": "INV-001",
        "invoice_date": "2026-02-03",
        "company": {
            "name": "Mcdonalds Ltd",
            "address": "123 Queen Street",
            "email": "billing@mcdonalds.co.nz",
        },
        "client": {
            "name": "Bronson Pieper",
            "address": "456 King Street",
            "email": "bronson@example.com",
        },
        "line_items": [
            {
                "description": "Consulting",
                "quantity": 2,
                "unit_price": 150.0,
            }
        ],
        "tax_rate": 0.15,
    }


def test_pdf_is_generated():
    invoice = generate_invoice(sample_invoice())

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "invoice.pdf")
        generate_invoice_pdf(invoice, path)

        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
