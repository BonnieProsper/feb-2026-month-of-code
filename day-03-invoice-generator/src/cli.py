import argparse
import json
import sys
from pathlib import Path
from glob import glob
from typing import List
from datetime import datetime

from src.validation import validate_invoice_data, ValidationError
from src.normalizer import normalize_invoice_json
from src.invoice_generator import InvoiceValidationError
from src.csv_loader import load_line_items_from_csv
from src.pdf_utils import generate_invoice_pdf
from src.reporting.totals import InvoiceTotals
from src.reporting.csv_export import export_totals_csv
from src.reporting.json_export import export_totals_json


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
    parser.add_argument("--output", help="Output PDF file (single invoice)")
    parser.add_argument("--output-dir", help="Output directory (batch invoices)")
    parser.add_argument("--check", action="store_true", help="Preview only (no PDF)")
    parser.add_argument("--theme", choices=["minimal", "modern"], default="minimal")
    parser.add_argument("--theme-config", help="Optional theme override JSON")
    parser.add_argument("--export-totals", help="Export totals (.csv or .json)")

    args = parser.parse_args()

    try:
        inputs = sorted(glob(args.input))
        if not inputs:
            raise ValueError(f"No input files matched: {args.input}")

        # Batch mode is explicit OR inferred
        is_batch = args.output_dir is not None or len(inputs) > 1

        # PDFs are generated only if:
        # - not preview mode
        # - not totals-only mode
        generate_pdfs = not args.check and args.export_totals is None

        if generate_pdfs:
            if is_batch and not args.output_dir:
                raise ValueError("--output-dir is required for batch PDF generation")
            if not is_batch and not args.output:
                raise ValueError("--output is required for single invoice PDF generation")

        all_totals: List[InvoiceTotals] = []

        for path in inputs:
            invoice = _load_invoice(path, args.format)

            invoice.calculate_totals()
            invoice.validate()

            all_totals.append(InvoiceTotals.from_invoice(invoice))

            if args.check:
                _print_preview(invoice, source=path)
                continue

            if generate_pdfs:
                if is_batch:
                    out_dir = Path(args.output_dir)
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_path = out_dir / f"{invoice.invoice_number}.pdf"
                else:
                    out_path = Path(args.output)

                generate_invoice_pdf(
                    invoice,
                    str(out_path),
                    theme_name=args.theme,
                    theme_override=args.theme_config,
                )

        # Export totals after processing
        if args.export_totals:
            _export_totals(all_totals, args.export_totals)

        # -------------------------
        # Completion message
        # -------------------------
        msg_parts = []

        if generate_pdfs:
            msg_parts.append(f"{len(inputs)} invoice(s) processed")
            if is_batch:
                msg_parts.append(f"PDFs in {args.output_dir}")
            else:
                msg_parts.append(f"PDF saved at {args.output}")
        elif args.check:
            msg_parts.append("Preview complete ✅")
        else:
            msg_parts.append(f"{len(inputs)} invoice(s) processed")

        if args.export_totals:
            msg_parts.append(f"Totals exported to {args.export_totals}")

        print(" | ".join(msg_parts))

    except (ValidationError, InvoiceValidationError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


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

    if not isinstance(raw, dict):
        raise ValueError(f"{path} is not a valid invoice JSON object")

    if "invoice_number" not in raw:
        raise ValueError(f"{path} does not appear to be an invoice file")

    validate_invoice_data(raw)
    return normalize_invoice_json(raw)

def _load_from_csv(path: str):
    validate_invoice_data(BASE_INVOICE_TEMPLATE, require_line_items=False)
    invoice = normalize_invoice_json(BASE_INVOICE_TEMPLATE)

    invoice.line_items = load_line_items_from_csv(path)

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

    print(f"\nSubtotal: {invoice.subtotal:.2f}")
    print(f"{invoice.tax_label}: {invoice.tax_amount:.2f}")
    print(f"Total: {invoice.total:.2f}\n")


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
