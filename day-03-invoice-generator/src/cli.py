# src/cli.py
import argparse
import json
import sys
from pathlib import Path

from src.validation import validate_invoice_data, ValidationError
from src.normalizer import normalize_invoice_json
from src.pdf_utils import generate_invoice_pdf
from src.invoice_generator import InvoiceValidationError


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a PDF invoice from a JSON definition"
    )
    parser.add_argument("--input", required=True, help="Path to invoice JSON file")
    parser.add_argument("--output", required=True, help="Path to output PDF file")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        with input_path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON ({e})", file=sys.stderr)
        sys.exit(1)

    try:
        # Schema-level validation
        validate_invoice_data(raw_data)

        # Domain construction
        invoice = normalize_invoice_json(raw_data)
        invoice.calculate_totals()
        invoice.validate()

        # Render
        generate_invoice_pdf(invoice, str(output_path))

    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except InvoiceValidationError as e:
        print(f"Invoice error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Invoice generated successfully → {output_path}")


if __name__ == "__main__":
    main()
