import tempfile
from pathlib import Path
from src.invoice_generator import Invoice, Party, LineItem
from src.pdf_utils import generate_invoice_pdf

def sample_invoice() -> Invoice:
    company = Party(name="Mcdonalds Ltd", address="123 Queen Street", email="billing@mcdonalds.co.nz")
    client = Party(name="Bronson Pieper", address="456 King Street", email="bronson@example.com")
    items = [LineItem(description="Consulting", quantity=2, unit_price=150.0)]
    invoice = Invoice(
        invoice_number="INV-001",
        invoice_date="2026-02-03",
        company=company,
        client=client,
        line_items=items,
        tax_rate=0.15,
    )
    invoice.calculate_totals()
    return invoice

def test_pdf_is_generated():
    invoice = sample_invoice()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "invoice.pdf"
        generate_invoice_pdf(invoice, str(path))
        assert path.exists()
        assert path.stat().st_size > 0
