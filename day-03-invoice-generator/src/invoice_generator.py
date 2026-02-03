from dataclasses import dataclass, field
from typing import List, Optional
from copy import deepcopy
from datetime import datetime, timedelta


@dataclass
class Party:
    name: str
    address: str
    email: str
    logo_path: Optional[str] = None  # Only for company


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float
    line_total: float = field(default=0.0)

class InvoiceValidationError(Exception):
    pass

@dataclass
class Invoice:
    invoice_number: str
    invoice_date: str
    company: Party
    client: Party
    line_items: List[LineItem]
    tax_rate: float
    tax_label: str = "Tax"
    subtotal: float = field(default=0.0)
    tax_amount: float = field(default=0.0)
    total: float = field(default=0.0)
    notes: Optional[str] = None
    due_date: Optional[str] = None
    currency_symbol: str = "$NZD"
    footer: Optional[str] = "Bank: ANZ 06-1234-5678-9012, SWIFT: ANZBNZ22"

    def validate(self) -> None:
        if not self.invoice_number:
            raise InvoiceValidationError("Invoice number required")

        if any(item.quantity <= 0 for item in self.line_items):
            raise InvoiceValidationError("Line item quantity must be positive")

        if round(self.subtotal + self.tax_amount, 2) != round(self.total, 2):
            raise InvoiceValidationError("Totals do not reconcile")

def generate_invoice(invoice_data: dict) -> dict:
    """
    Return a new invoice dict with calculated line totals, subtotal, tax, total, and due date.
    """
    invoice = deepcopy(invoice_data)

    # Calculate line totals safely
    for item in invoice["line_items"]:
        qty = item.get("quantity") or 0.0
        price = item.get("unit_price") or 0.0
        item["line_total"] = round(qty * price, 2)

    # Safe subtotal, tax, total
    subtotal = sum(item["line_total"] for item in invoice["line_items"])
    tax_amount = round(subtotal * (invoice.get("tax_rate") or 0.0), 2)
    total = round(subtotal + tax_amount, 2)

    invoice["subtotal"] = round(subtotal, 2)
    invoice["tax_amount"] = tax_amount
    invoice["total"] = total

    # Add due_date if missing
    if "invoice_date" in invoice and "due_date" not in invoice:
        try:
            invoice_date_obj = datetime.strptime(invoice["invoice_date"], "%Y-%m-%d")
            due_date_obj = invoice_date_obj + timedelta(days=14)
            invoice["due_date"] = due_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            invoice["due_date"] = None

    return invoice


def calculate_invoice_totals(invoice: Invoice) -> None:
    """
    Recalculate totals for an Invoice dataclass.
    Modifies invoice in-place safely.
    """
    for item in invoice.line_items:
        item.line_total = round(item.quantity * item.unit_price, 2)

    invoice.subtotal = round(sum(item.line_total for item in invoice.line_items), 2)
    invoice.tax_amount = round(invoice.subtotal * invoice.tax_rate, 2)
    invoice.total = round(invoice.subtotal + invoice.tax_amount, 2)
