import argparse
import json
import sys

from src.validation import validate_invoice_data, ValidationError
from src.invoice_generator import generate_invoice
from src.pdf_utils import generate_invoice_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a PDF invoice from a JSON file"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to invoice JSON file",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output PDF file",
    )

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            invoice_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON file ({e})", file=sys.stderr)
        sys.exit(1)

    try:
        validate_invoice_data(invoice_data)
        invoice = generate_invoice(invoice_data)
        generate_invoice_pdf(invoice, args.output)
    except ValidationError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Invoice generated successfully: {args.output}")


if __name__ == "__main__":
    main()
