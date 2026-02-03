import argparse
import json
import sys
from pathlib import Path
from glob import glob
from typing import List
from datetime import datetime

from src.validation import validate_invoice_data, ValidationError
from src.normalizer import normalize_invoice_json
from src.invoice_generator import InvoiceValidationError, Invoice
from src.csv_loader import load_line_items_from_csv
from src.pdf_utils import generate_invoice_pdf
from src.reporting.totals import InvoiceTotals
from src.reporting.csv_export import export_totals_csv
from src.reporting.json_export import export_totals_json
from src.themes import load_theme


BASE_INVOICE_TEMPLATE = {
    "invoice_number": "INV-000",
    "invoice_date": "2026-01-01",
    "company": {
        "name": "Your Company",
        "address": "123 Street\nCity 0000\nCountry",
        "email": "accounts@example.com",
        "logo_path": None,
    },
    "client": {
        "name": "Client Name",
        "address": "Client Address\nCity 0000\nCountry",
        "email": "client@example.com",
    },
    "tax_rate": 0.0,
    "tax_label": "Tax",
    "line_items": [],
    "notes": None,
    "footer": "Bank details: ...",
}


# =========================
# CLI ENTRYPOINT
# =========================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate professional PDF invoices from JSON or CSV data"
    )

    parser.add_argument("--input", required=True, help="Input file path or glob")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", help="Output PDF file (single mode)")
    parser.add_argument("--output-dir", help="Output directory (batch mode)")
    parser.add_argument("--check", action="store_true", help="Preview only (no PDF)")
    parser.add_argument("--theme", choices=["minimal", "modern"], default="minimal")
    parser.add_argument("--theme-config", help="Optional theme override JSON")
    parser.add_argument("--export-totals", help="Export totals (.csv or .json)")

    args = parser.parse_args()

    try:
        inputs = sorted(glob(args.input))
        if not inputs:
            raise ValueError(f"No input files matched: {args.input}")

        is_batch = len(inputs) > 1

        if is_batch and not args.output_dir and not args.check:
            raise ValueError("--output-dir is required for batch PDF generation")

        all_totals: List[InvoiceTotals] = []

        for path in inputs:
            invoice = _load_invoice(path, args.format)

            invoice.calculate_totals()
            invoice.validate()

            totals = InvoiceTotals.from_invoice(invoice)
            all_totals.append(totals)

            if args.check:
                _print_preview(invoice, source=path)
                continue

            if is_batch:
                out_path = Path(args.output_dir) / f"{invoice.invoice_number}.pdf"
            else:
                if not args.output:
                    raise ValueError("--output is required unless --check is used")
                out_path = Path(args.output)

            generate_invoice_pdf(invoice, str(out_path), theme_name=args.theme, theme_override=args.theme_config)

        if args.export_totals:
            _export_totals(all_totals, args.export_totals)

    except (ValidationError, InvoiceValidationError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print("Done.")


# =========================
# LOADERS
# =========================

def _load_invoice(path: str, fmt: str):
    if fmt == "json":
        return _load_from_json(path)
    if fmt == "csv":
        return _load_from_csv(path)
    raise ValueError(f"Unsupported format: {fmt}")


def _load_from_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    validate_invoice_data(raw)
    return normalize_invoice_json(raw)


def _load_from_csv(path: str):
    validate_invoice_data(BASE_INVOICE_TEMPLATE, require_line_items=False)

    invoice = normalize_invoice_json(BASE_INVOICE_TEMPLATE)
    invoice.line_items = load_line_items_from_csv(path)

    # derive invoice metadata from filename
    stem = Path(path).stem
    invoice.invoice_number = stem.upper()
    invoice.invoice_date = datetime.today().strftime("%Y-%m-%d")

    return invoice


# =========================
# PREVIEW
# =========================

def _print_preview(invoice, source: str) -> None:
    if not hasattr(invoice, "total"):
        invoice.calculate_totals()
    print("\n" + "=" * 50)
    print(f"INVOICE PREVIEW → {source}")
    print("=" * 50)

    for item in invoice.line_items:
        print(
            f"- {item.description}\n"
            f"  {item.quantity} × {item.unit_price:.2f} = {item.line_total:.2f}"
        )

    print()
    print(f"Subtotal: {invoice.subtotal:.2f}")
    print(f"{invoice.tax_label}: {invoice.tax_amount:.2f}")
    print(f"Total: {invoice.total:.2f}")
    print()


# =========================
# TOTALS EXPORT
# =========================

def _export_totals(totals: List[InvoiceTotals], path: str) -> None:
    if path.endswith(".csv"):
        export_totals_csv(totals, path)
    elif path.endswith(".json"):
        export_totals_json(totals, path)
    else:
        raise ValueError("Totals export must be .csv or .json")


if __name__ == "__main__":
    main()