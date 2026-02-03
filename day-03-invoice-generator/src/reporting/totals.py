# src/reporting/totals.py
from dataclasses import dataclass
from typing import Dict
from src.invoice_generator import Invoice


@dataclass(frozen=True)
class InvoiceTotals:
    invoice_number: str
    subtotal: float
    tax: float
    total: float

    @classmethod
    def from_invoice(cls, invoice: Invoice) -> "InvoiceTotals":
        if not hasattr(invoice, "total"):
            raise ValueError("Invoice totals have not been calculated")

        return cls(
            invoice_number=invoice.invoice_number,
            subtotal=invoice.subtotal,
            tax=invoice.tax_amount,
            total=invoice.total,
        )


    def to_dict(self) -> Dict[str, float | str]:
        return {
            "invoice_number": self.invoice_number,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total,
        }
