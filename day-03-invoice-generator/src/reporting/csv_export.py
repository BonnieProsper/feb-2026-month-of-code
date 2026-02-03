# src/reporting/csv_export.py
import csv
from pathlib import Path
from typing import List

from src.reporting.totals import InvoiceTotals


CSV_HEADERS = ["invoice_number", "subtotal", "tax", "total"]


def export_totals_csv(
    totals: List[InvoiceTotals],
    path: str,
) -> None:
    out = Path(path)

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()

        for t in totals:
            writer.writerow(t.to_dict())
