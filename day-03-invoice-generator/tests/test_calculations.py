from src.invoice_generator import Invoice, Party, LineItem

def base_invoice() -> Invoice:
    company = Party(name="Manning Ltd", address="123 Queen Street", email="billing@manning.co.nz")
    client = Party(name="Bronson Pieper", address="456 King Street", email="bronson@example.com")
    items = [LineItem(description="Consulting work", quantity=5, unit_price=100.0)]
    return Invoice(
        invoice_number="INV-001",
        invoice_date="2026-02-03",
        company=company,
        client=client,
        line_items=items,
        tax_rate=0.15,
    )

def test_line_total_calculation():
    invoice = base_invoice()
    invoice.calculate_totals()
    assert invoice.line_items[0].line_total == 500.0

def test_subtotal_calculation():
    invoice = base_invoice()
    invoice.calculate_totals()
    assert invoice.subtotal == 500.0

def test_tax_calculation():
    invoice = base_invoice()
    invoice.calculate_totals()
    assert invoice.tax_amount == 75.0

def test_total_calculation():
    invoice = base_invoice()
    invoice.calculate_totals()
    assert invoice.total == 575.0