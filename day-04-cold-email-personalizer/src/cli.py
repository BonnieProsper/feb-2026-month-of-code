import argparse
import sys
from pathlib import Path
from typing import List, Dict

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

        # Deterministic ordering for stable output
        prospects = sorted(
            prospects,
            key=lambda p: (p.get("company", ""), p.get("first_name", "")),
        )

        if args.preview:
            _handle_preview(
                template_text,
                prospects,
                placeholders,
                args.preview,
            )
            return

        rendered_emails: List[str] = []
        skipped = 0

        for prospect in prospects:
            try:
                rendered_emails.append(
                    render_template(
                        template_text,
                        prospect,
                        required_placeholders=placeholders,
                    )
                )
            except TemplateError:
                skipped += 1
                if args.verbose:
                    print(
                        f"Skipping prospect: {prospect}",
                        file=sys.stderr,
                    )

        if not rendered_emails:
            print("No emails rendered.", file=sys.stderr)
            sys.exit(2)

        if args.dry_run:
            print(
                f"Dry run: {len(rendered_emails)} emails would be rendered "
                f"({skipped} skipped)."
            )
            sys.exit(0)

        metrics = render_outputs(
            rendered_emails=rendered_emails,
            prospects=prospects[: len(rendered_emails)],
            output_dir=args.output_dir,
            combined_output_path=args.combined_output,
        )

        print(
            f"Rendered {metrics['rendered']} emails "
            f"({metrics['skipped']} skipped)."
        )
        print(f"Output directory: {args.output_dir}")

        sys.exit(0)

    except (DataLoadError, ValidationError, TemplateError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _handle_preview(
    template_text: str,
    prospects: List[Dict[str, str]],
    placeholders: set[str],
    preview_index: int,
) -> None:
    index = preview_index - 1
    if index < 0 or index >= len(prospects):
        raise ValidationError(
            f"Preview index {preview_index} is out of range."
        )

    rendered = render_template(
        template_text,
        prospects[index],
        required_placeholders=placeholders,
    )
    print(rendered)


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
        "--dry-run",
        action="store_true",
        help="Validate and report without writing any files.",
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
