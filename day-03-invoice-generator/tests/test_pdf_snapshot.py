from pathlib import Path
import json

from pdfminer.high_level import extract_text

from src.normalizer import normalize_invoice_json
from src.invoice_generator import Party, LineItem, Invoice
from src.pdf_utils import generate_invoice_pdf
from src.validation import validate_invoice_data


FIXTURES = Path("data")
SNAPSHOTS = Path("tests/snapshots")
OUTPUT = Path("tests/_tmp")

OUTPUT.mkdir(exist_ok=True)


def normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line.strip())


def test_invoice_pdf_snapshot():
    input_json = FIXTURES / "sample_invoice.json"
    output_pdf = OUTPUT / "sample_invoice.pdf"
    snapshot_file = SNAPSHOTS / "sample_invoice.txt"

    raw = json.loads(input_json.read_text(encoding="utf-8"))
    validate_invoice_data(raw)

    invoice = normalize_invoice_json(raw)
    invoice.calculate_totals()
    invoice.validate()

    generate_invoice_pdf(invoice, str(output_pdf))
    assert output_pdf.exists()

    extracted = extract_text(str(output_pdf))
    normalized = normalize_text(extracted)

    if not snapshot_file.exists():
        snapshot_file.write_text(normalized, encoding="utf-8")
        raise AssertionError("Snapshot created. Re-run tests.")

    expected = snapshot_file.read_text(encoding="utf-8")
    assert normalized == expected


def test_pdf_generation_smoke():
    company = Party(name="Test Co", address="123 Street", email="a@test.com")
    client = Party(name="Client Co", address="456 Avenue", email="b@test.com")
    items = [LineItem(description="Service", quantity=2, unit_price=100)]

    invoice = Invoice(
        invoice_number="TST-001",
        invoice_date="2026-02-03",
        company=company,
        client=client,
        line_items=items,
        tax_rate=0.1,
    )

    invoice.calculate_totals()

    output_pdf = OUTPUT / "smoke_test.pdf"
    generate_invoice_pdf(invoice, str(output_pdf))

    text = extract_text(str(output_pdf))
    assert "TST-001" in text
    assert "Service" in text
    assert "200.00" in text
    assert "Subtotal" in text
    assert "Tax" in text
    assert "Total" in text
