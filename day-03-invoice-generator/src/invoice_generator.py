from copy import deepcopy


def generate_invoice(invoice_data: dict) -> dict:
    """
    Return a new invoice dict with calculated line totals,
    subtotal, tax amount, and final total.
    """
    invoice = deepcopy(invoice_data)

    for item in invoice["line_items"]:
        item["line_total"] = _calculate_line_total(item)

    subtotal = _calculate_subtotal(invoice["line_items"])
    tax_amount = _calculate_tax(subtotal, invoice["tax_rate"])
    total = subtotal + tax_amount

    invoice["subtotal"] = round(subtotal, 2)
    invoice["tax_amount"] = round(tax_amount, 2)
    invoice["total"] = round(total, 2)

    return invoice


def _calculate_line_total(item: dict) -> float:
    return item["quantity"] * item["unit_price"]


def _calculate_subtotal(items: list) -> float:
    return sum(item["line_total"] for item in items)


def _calculate_tax(subtotal: float, tax_rate: float) -> float:
    return subtotal * tax_rate
