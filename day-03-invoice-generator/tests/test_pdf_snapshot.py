from pathlib import Path

from pdfminer.high_level import extract_text 

from src.normalizer import normalize_invoice_json
from src.invoice_generator import InvoiceValidationError
from src.pdf_utils import generate_invoice_pdf
from src.validation import validate_invoice_data


FIXTURES = Path("data")
SNAPSHOTS = Path("tests/snapshots")
OUTPUT = Path("tests/_tmp")

OUTPUT.mkdir(exist_ok=True)


def normalize_text(text: str) -> str:
    """
    Normalize extracted PDF text so snapshots are stable.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line.strip())


def test_invoice_pdf_snapshot():
    input_json = FIXTURES / "sample_invoice.json"
    output_pdf = OUTPUT / "sample_invoice.pdf"
    snapshot_file = SNAPSHOTS / "sample_invoice.txt"

    # Load + validate input
    raw = input_json.read_text(encoding="utf-8")
    data = __import__("json").loads(raw)

    validate_invoice_data(data)

    invoice = normalize_invoice_json(data)
    invoice.calculate_totals()
    invoice.validate()

    # Generate PDF
    generate_invoice_pdf(invoice, str(output_pdf))

    assert output_pdf.exists(), "PDF was not generated"

    # Extract text
    extracted = extract_text(str(output_pdf))
    normalized = normalize_text(extracted)

    # Snapshot comparison
    if not snapshot_file.exists():
        snapshot_file.write_text(normalized, encoding="utf-8")
        raise AssertionError(
            "Snapshot created. Re-run tests to validate output."
        )

    expected = snapshot_file.read_text(encoding="utf-8")

    assert normalized == expected
