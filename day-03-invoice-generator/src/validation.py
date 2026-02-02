class ValidationError(Exception):
    """Raised when invoice input data is invalid."""
    pass


def validate_invoice_data(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValidationError("Invoice data must be a JSON object")

    _validate_required_fields(data)
    _validate_company(data["company"])
    _validate_client(data["client"])
    _validate_line_items(data["line_items"])
    _validate_tax_rate(data["tax_rate"])


def _validate_required_fields(data: dict) -> None:
    required_fields = [
        "invoice_number",
        "invoice_date",
        "company",
        "client",
        "line_items",
        "tax_rate",
    ]

    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: '{field}'")


def _validate_company(company: dict) -> None:
    _validate_party(company, party_name="company")


def _validate_client(client: dict) -> None:
    _validate_party(client, party_name="client")


def _validate_party(party: dict, party_name: str) -> None:
    if not isinstance(party, dict):
        raise ValidationError(f"'{party_name}' must be an object")

    required_fields = ["name", "address", "email"]

    for field in required_fields:
        if field not in party:
            raise ValidationError(
                f"Missing required field in {party_name}: '{field}'"
            )
        if not isinstance(party[field], str) or not party[field].strip():
            raise ValidationError(
                f"'{party_name}.{field}' must be a non-empty string"
            )


def _validate_line_items(items: list) -> None:
    if not isinstance(items, list):
        raise ValidationError("'line_items' must be a list")

    if not items:
        raise ValidationError("'line_items' must contain at least one item")

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError(
                f"Line item at index {index} must be an object"
            )

        _validate_line_item(item, index)


def _validate_line_item(item: dict, index: int) -> None:
    required_fields = ["description", "quantity", "unit_price"]

    for field in required_fields:
        if field not in item:
            raise ValidationError(
                f"Missing field '{field}' in line item at index {index}"
            )

    if not isinstance(item["description"], str) or not item["description"].strip():
        raise ValidationError(
            f"'description' in line item {index} must be a non-empty string"
        )

    if not isinstance(item["quantity"], (int, float)) or item["quantity"] <= 0:
        raise ValidationError(
            f"'quantity' in line item {index} must be a number greater than 0"
        )

    if not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
        raise ValidationError(
            f"'unit_price' in line item {index} must be a non-negative number"
        )


def _validate_tax_rate(tax_rate) -> None:
    if not isinstance(tax_rate, (int, float)):
        raise ValidationError("'tax_rate' must be a number")

    if tax_rate < 0 or tax_rate > 1:
        raise ValidationError("'tax_rate' must be between 0 and 1")
