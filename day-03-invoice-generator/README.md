# Automated Invoice Generator (CLI)

A small, production‑style command‑line tool that generates professional PDF invoices from structured JSON input.

This project is intentionally scoped to demonstrate practical engineering judgment: clear data contracts, explicit validation, testable business logic, and a clean CLI interface. It is not a full invoicing platform.

---

## What This Tool Does

* Reads a single invoice described in JSON
* Validates required fields and data types
* Calculates subtotal, tax, and total
* Generates a clean, readable PDF invoice
* Optionally includes company branding (logo)

The tool is deterministic: the same input always produces the same output.

---

## What This Tool Does *Not* Do

* No web interface or GUI
* No batch processing
* No multi‑currency support
* No email sending or payment handling
* No complex templating or theming engine

These are deliberate scope decisions.

---

## Project Structure

```
day-03-invoice-generator/
├── src/
│   ├── cli.py
│   ├── invoice_generator.py
│   ├── pdf_utils.py
│   ├── validation.py
│   └── __init__.py
├── tests/
│   ├── test_validation.py
│   ├── test_calculations.py
│   └── __init__.py
├── data/
│   ├── sample_invoice.json
│   └── sample_invoice.pdf
├── requirements.txt
└── README.md
```

---

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# or
.venv\Scripts\Activate.ps1  # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Generate a PDF invoice from a JSON file:

```bash
python -m src.cli \
  --input data/sample_invoice.json \
  --output data/sample_invoice.pdf
```

On success:

```text
Invoice generated successfully: data/sample_invoice.pdf
```

---

## Input JSON Schema

### Required Top‑Level Fields

* `invoice_number` (string)
* `invoice_date` (string)
* `company` (object)
* `client` (object)
* `line_items` (non‑empty list)
* `tax_rate` (number between 0 and 1)

### Company / Client Object

```json
{
  "name": "Acme Ltd",
  "address": "123 Queen Street",
  "email": "billing@acme.co.nz",
  "logo_path": "data/logo.png"  // optional (company only)
}
```

### Line Item Object

```json
{
  "description": "Consulting work",
  "quantity": 5,
  "unit_price": 100.0
}
```

All monetary values are calculated by the tool. Totals are not accepted as input.

---

## Testing

Run all tests:

```bash
pytest
```

Test coverage includes:

* JSON input validation
* Invoice subtotal, tax, and total calculations
* PDF generation sanity check (file creation)

Tests are deterministic and do not rely on external services.

---

## Design Notes

* Validation is explicit and strict (no type coercion)
* Business logic is pure and side‑effect free
* PDF rendering is isolated from calculations
* CLI is thin glue code only

The architecture favors clarity and correctness over flexibility.

---

## Limitations & Future Improvements

* Single‑page invoices only
* Single tax rate per invoice
* Minimal PDF layout (no themes)

Potential extensions include invoice auto‑numbering, CSV export, and basic theming, all without changing core logic.

