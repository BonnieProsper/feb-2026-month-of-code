from typing import List
from src.invoice_generator import Invoice, Party, LineItem


def normalize_invoice_json(raw_json: dict) -> Invoice:
    """
    Convert external JSON into canonical Invoice dataclass.
    Handles aliases and ensures no None values for sums.
    """
    company_data = raw_json.get("company") or raw_json.get("seller")
    if company_data is None:
        raise ValueError("Missing company/seller info")

    client_data = raw_json.get("client") or raw_json.get("customer")
    if client_data is None:
        raise ValueError("Missing client/customer info")

    items_data = raw_json.get("line_items") or raw_json.get("items") or []
    if not items_data:
        raise ValueError("Missing line_items/items data")

    line_items: List[LineItem] = []
    for item in items_data:
        qty = item.get("quantity") or 0.0
        price = item.get("unit_price") or 0.0
        line_items.append(
            LineItem(
                description=item.get("description", ""),
                quantity=qty,
                unit_price=price,
                line_total=round(qty * price, 2)
            )
        )

    invoice_date: str = raw_json.get("invoice_date") or raw_json.get("issue_date") or ""
    if not invoice_date:
        raise ValueError("Missing invoice_date/issue_date")

    tax_rate: float = raw_json.get("tax_rate") or raw_json.get("gst") or 0.0

    subtotal = round(sum(li.line_total for li in line_items), 2)
    tax_amount = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax_amount, 2)

    company = Party(
        name=company_data.get("name", ""),
        address=company_data.get("address", ""),
        email=company_data.get("email", ""),
        logo_path=company_data.get("logo_path")
    )

    client = Party(
        name=client_data.get("name", ""),
        address=client_data.get("address", ""),
        email=client_data.get("email", "")
    )

    return Invoice(
        invoice_number=raw_json.get("invoice_number", "UNKNOWN"),
        invoice_date=invoice_date,
        company=company,
        client=client,
        line_items=line_items,
        tax_rate=tax_rate,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        notes=raw_json.get("notes"),
        due_date=raw_json.get("due_date")
    )
