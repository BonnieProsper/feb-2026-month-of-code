from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta


# ================= Exceptions =================

class InvoiceValidationError(Exception):
    pass


# ================= Core Models =================

@dataclass
class Party:
    name: str
    address: str
    email: Optional[str] = None
    logo_path: Optional[str] = None  # Company only


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float
    line_total: float = field(init=False)

    def calculate_total(self) -> None:
        if self.quantity <= 0:
            raise InvoiceValidationError("Line item quantity must be positive")
        if self.unit_price < 0:
            raise InvoiceValidationError("Unit price cannot be negative")

        self.line_total = round(self.quantity * self.unit_price, 2)


@dataclass
class Invoice:
    invoice_number: str
    invoice_date: str  # ISO string
    company: Party
    client: Party
    line_items: List[LineItem]
    tax_rate: float

    tax_label: str = "Tax"
    notes: Optional[str] = None
    footer: Optional[str] = None
    due_date: Optional[str] = None

    subtotal: float = field(init=False)
    tax_amount: float = field(init=False)
    total: float = field(init=False)

    # ---------- Construction ----------

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        try:
            company = Party(**data["company"])
            client = Party(**data["client"])
            items = [LineItem(**item) for item in data["line_items"]]
        except (KeyError, TypeError) as e:
            raise InvoiceValidationError(f"Invalid invoice structure: {e}")

        invoice = cls(
            invoice_number=data["invoice_number"],
            invoice_date=data["invoice_date"],
            company=company,
            client=client,
            line_items=items,
            tax_rate=data.get("tax_rate", 0.0),
            tax_label=data.get("tax_label", "Tax"),
            notes=data.get("notes"),
            footer=data.get("footer"),
            due_date=data.get("due_date"),
        )

        invoice._ensure_due_date()
        return invoice

    # ---------- Calculation ----------

    def calculate_totals(self) -> None:
        for item in self.line_items:
            item.calculate_total()

        self.subtotal = round(sum(item.line_total for item in self.line_items), 2)
        self.tax_amount = round(self.subtotal * self.tax_rate, 2)
        self.total = round(self.subtotal + self.tax_amount, 2)

    # ---------- Validation ----------

    def validate(self) -> None:
        if not self.invoice_number:
            raise InvoiceValidationError("Invoice number is required")

        if not self.line_items:
            raise InvoiceValidationError("Invoice must contain at least one line item")

        try:
            datetime.strptime(self.invoice_date, "%Y-%m-%d")
        except ValueError:
            raise InvoiceValidationError("invoice_date must be YYYY-MM-DD")

        # Financial consistency
        if round(self.subtotal + self.tax_amount, 2) != round(self.total, 2):
            raise InvoiceValidationError("Invoice totals do not reconcile")

    # ---------- Helpers ----------

    def _ensure_due_date(self) -> None:
        if self.due_date:
            return

        try:
            invoice_dt = datetime.strptime(self.invoice_date, "%Y-%m-%d")
            self.due_date = (invoice_dt + timedelta(days=14)).strftime("%Y-%m-%d")
        except ValueError:
            self.due_date = None
