import argparse
import sys
from pathlib import Path

from src.template_engine import extract_placeholders, render_template
from src.loader import load_prospects
from src.validation import validate_prospects
from src.renderer import render_outputs
from src.errors import DataLoadError, ValidationError, TemplateError


def main() -> None:
    args = _parse_args()

    try:
        template_text = _read_template(args.template)
        placeholders = extract_placeholders(template_text)

        prospects = load_prospects(args.data)
        validate_prospects(prospects, placeholders)

        if args.preview:
            index = args.preview - 1
            if index < 0 or index >= len(prospects):
                raise ValidationError(
                    f"Preview index {args.preview} is out of range."
                )

            rendered = render_template(
                template_text,
                prospects[index],
                required_placeholders=placeholders,
            )
            print(rendered)
            return

        rendered_emails = [
            render_template(
                template_text,
                prospect,
                required_placeholders=placeholders,
            )
            for prospect in prospects
        ]

        metrics = render_outputs(
            rendered_emails=rendered_emails,
            prospects=prospects,
            output_dir=args.output_dir,
            combined_output_path=args.combined_output,
        )

        print(
            f"Rendered {metrics['rendered']} emails "
            f"({metrics['skipped']} skipped)."
        )

    except (DataLoadError, ValidationError, TemplateError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate personalized cold emails from a template and prospect data."
    )

    parser.add_argument(
        "--template",
        required=True,
        help="Path to the email template file (.txt or .md).",
    )

    parser.add_argument(
        "--data",
        required=True,
        help="Path to prospect data file (.csv or .json).",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write rendered emails.",
    )

    parser.add_argument(
        "--combined-output",
        help="Optional path to write all emails into a single file.",
    )

    parser.add_argument(
        "--preview",
        type=int,
        help="Render a single prospect to stdout (1-based index).",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress and warnings.",
    )

    return parser.parse_args()


def _read_template(path: str) -> str:
    template_path = Path(path)

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    content = template_path.read_text(encoding="utf-8")

    if not content.strip():
        raise ValueError("Template file is empty.")

    return content


if __name__ == "__main__":
    main()
