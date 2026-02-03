# Automated Invoice Generator (CLI)

A small, production‑style command‑line tool that generates professional PDF invoices from structured JSON input.

This project is intentionally scoped to demonstrate practical engineering judgment: clear data contracts, explicit validation, testable business logic, and a clean CLI interface. It is not a full invoicing platform.

---

## Features

- Read invoices from JSON or CSV input
- Validate required fields and data types
- Calculate subtotal, tax, and total
- Generate clean, readable PDF invoices
- Batch PDF generation
- Export invoice totals to CSV or JSON
- Optional minimal theming for PDF output
- Deterministic behavior: same input → same output

---

## Non-Features/Scope Limitations

- No web interface or GUI
- No multi-currency support
- No email sending or payment handling
- Minimal PDF layout; no complex templating
- Single-page invoices only

These are deliberate scope decisions to keep the tool simple, reliable, and testable.

---

## Project Structure

```
day-03-invoice-generator/
├── src/
│ ├── cli.py
│ ├── invoice_generator.py
│ ├── pdf_utils.py
│ ├── validation.py
│ ├── csv_loader.py
│ ├── normalizer.py
│ ├── reporting/
│ │ ├── totals.py
│ │ ├── csv_export.py
│ │ ├── json_export.py
│ ├── themes.py
│ └── __init__.py
├── tests/
│ ├── test_pdf_snapshot.py
│ ├── test_pdf_generation.py
│ ├── test_calculations.py
│ └── __init__.py
├── data/
│ ├── sample_invoice.json
│ └── sample_invoice.pdf
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

Batch generate PDFs from multiple files:
```bash
python -m src.cli \
  --input "data/invoices/*.json" \
  --output-dir data/output_pdfs
```

Check invoices without generating PDFs:
```bash
python -m src.cli --input data/sample_invoice.json --check
```

Export invoice totals:
```bash
python -m src.cli \
  --input "data/invoices/*.json" \
  --output-dir output/pdfs \
  --export-totals output/totals.csv
```

Generated totals files should not be placed in the same directory as invoice input files when using glob patterns (e.g. data/*.json)

## Input Formats
### JSON

Required top-level fields:
- invoice_number (string)
- invoice_date (YYYY-MM-DD string)
- company (object)
- client (object)
- line_items (non-empty list)
- tax_rate (number between 0 and 1)

Company/Client object:
```json
{
  "name": "Manning Ltd",
  "address": "123 Queen Street",
  "email": "billing@manning.co.nz",
  "logo_path": "data/logo.png"  // optional (company only)
}
```

Line item object:
```json
{
  "description": "Consulting work",
  "quantity": 5,
  "unit_price": 100.0
}
```

### CSV

- Each row represents a line item
- Metadata (invoice number, date, company, client) is derived from an internal base template and the input filename.
- Supports batch processing

## Testing

Run all tests:
```bash
pytest
```

Tests cover:
- JSON/CSV validation
- Invoice calculations (line totals, subtotal, tax, total)
- PDF generation and snapshot comparison
- CSV/JSON totals export

Tests are deterministic, do not rely on external services, and validate batch behavior.

## Design Principles

- Explicit validation, no type coercion
-  PDF rendering isolated
- Thin CLI glue layer
- Deterministic output; reproducible results

## Limitations & Future Improvements

- Multi-page invoices
- Multiple tax rates
- Advanced theming or templating
- Auto-increment invoice numbering
- Email sending or payment integration

These can be added without changing core logic.