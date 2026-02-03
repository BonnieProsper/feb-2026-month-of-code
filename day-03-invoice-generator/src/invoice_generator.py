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
    invoice_date: str  # YYYY-MM-DD
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

    # ---------- Calculation ----------

    def calculate_totals(self) -> None:
        if not self.line_items:
            raise InvoiceValidationError("Invoice must contain at least one line item")

        for item in self.line_items:
            item.calculate_total()

        self.subtotal = round(sum(i.line_total for i in self.line_items), 2)
        self.tax_amount = round(self.subtotal * self.tax_rate, 2)
        self.total = round(self.subtotal + self.tax_amount, 2)

        self._ensure_due_date()

    # ---------- Validation ----------

    def validate(self) -> None:
        if not self.invoice_number:
            raise InvoiceValidationError("Invoice number is required")

        try:
            datetime.strptime(self.invoice_date, "%Y-%m-%d")
        except ValueError:
            raise InvoiceValidationError("invoice_date must be YYYY-MM-DD")

        if not hasattr(self, "total"):
            raise InvoiceValidationError("Totals have not been calculated")

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
