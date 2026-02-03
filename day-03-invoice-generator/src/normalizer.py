from typing import List
from src.invoice_generator import Invoice, Party, LineItem, InvoiceValidationError


def normalize_invoice_json(raw_json: dict) -> Invoice:
    """
    Convert external JSON into a canonical Invoice object.
    Handles field aliases and structural cleanup only.
    """

    company_data = raw_json.get("company") or raw_json.get("seller")
    if not isinstance(company_data, dict):
        raise InvoiceValidationError("Missing or invalid company/seller data")

    client_data = raw_json.get("client") or raw_json.get("customer")
    if not isinstance(client_data, dict):
        raise InvoiceValidationError("Missing or invalid client/customer data")

    items_data = raw_json.get("line_items") or raw_json.get("items") or []

    if not isinstance(items_data, list):
        raise InvoiceValidationError("Invalid line_items/items data")

    line_items: List[LineItem] = []
    for item in items_data:
        line_items.append(
            LineItem(
                description=str(item.get("description", "")).strip(),
                quantity=float(item.get("quantity", 0)),
                unit_price=float(item.get("unit_price", 0)),
            )
        )

    invoice_date = (
        raw_json.get("invoice_date")
        or raw_json.get("issue_date")
        or ""
    )

    if not invoice_date:
        raise InvoiceValidationError("Missing invoice_date/issue_date")

    company = Party(
        name=company_data.get("name", "").strip(),
        address=company_data.get("address", "").strip(),
        email=company_data.get("email"),
        logo_path=company_data.get("logo_path"),
    )

    client = Party(
        name=client_data.get("name", "").strip(),
        address=client_data.get("address", "").strip(),
        email=client_data.get("email"),
    )

    return Invoice(
        invoice_number=raw_json.get("invoice_number", "").strip(),
        invoice_date=invoice_date,
        company=company,
        client=client,
        line_items=line_items,
        tax_rate=float(raw_json.get("tax_rate", raw_json.get("gst", 0.0))),
        tax_label=raw_json.get("tax_label", "Tax"),
        notes=raw_json.get("notes"),
        footer=raw_json.get("footer"),
        due_date=raw_json.get("due_date"),
    )
