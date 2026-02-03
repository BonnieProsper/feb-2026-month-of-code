# src/reporting/json_export.py
import json
from pathlib import Path
from typing import List

from src.reporting.totals import InvoiceTotals


def export_totals_json(totals: List[InvoiceTotals], path: str) -> None:
    out = Path(path)

    data = [t.to_dict() for t in totals]

    out.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
