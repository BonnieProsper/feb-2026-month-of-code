# src/csv_loader.py
import csv
from typing import List

from src.invoice_generator import LineItem


QUANTITY_ALIASES = {"quantity", "qty", "amount"}
PRICE_ALIASES = {"unit_price", "price", "unit_cost"}


def load_line_items_from_csv(path: str) -> List[LineItem]:
    items: List[LineItem] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV file has no headers")

        headers = {h.lower().strip(): h for h in reader.fieldnames}

        def find_col(aliases):
            for key in aliases:
                if key in headers:
                    return headers[key]
            return None

        desc_col = headers.get("description")
        qty_col = find_col(QUANTITY_ALIASES)
        price_col = find_col(PRICE_ALIASES)

        if not desc_col or not qty_col or not price_col:
            raise ValueError(
                "CSV must contain description, quantity, and unit_price columns"
            )

        for row_num, row in enumerate(reader, start=2):
            description = (row.get(desc_col) or "").strip()
            if not description:
                continue

            try:
                qty = float(row[qty_col])
                price = float(row[price_col])
            except (TypeError, ValueError):
                raise ValueError(f"Invalid numeric value on row {row_num}")

            items.append(
                LineItem(
                    description=description,
                    quantity=qty,
                    unit_price=price,
                )
            )

    if not items:
        raise ValueError("CSV contains no valid line items")

    return items
