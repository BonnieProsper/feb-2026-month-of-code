# src/cli.py

import argparse
import sys
from pathlib import Path

from src.loader import load_prospects
from src.validation import validate_prospects
from src.template_engine import parse_template
from src.renderer import render_outputs
from src.errors import DataLoadError, ValidationError, TemplateError


def main() -> None:
    args = _parse_args()

    try:
        template_text = _read_template(args.template)
        parsed_template = parse_template(template_text)

        prospects = load_prospects(args.data)

        validation_result = validate_prospects(
            prospects=prospects,
            required_fields=parsed_template.placeholders,
        )

        valid_prospects = validation_result.valid_prospects

        if args.verbose:
            for skipped in validation_result.skipped_prospects:
                company = skipped.prospect.get("company", "<unknown>")
                print(
                    f"Skipping prospect #{skipped.index} ({company}): {skipped.reason}",
                    file=sys.stderr,
                )

        # -----------------------------
        # Preview mode
        # -----------------------------
        if args.preview:
            _handle_preview(
                parsed_template=parsed_template,
                prospects=valid_prospects,
                preview_index=args.preview,
            )
            sys.exit(0)

        if not valid_prospects:
            print("All prospects were skipped.", file=sys.stderr)
            sys.exit(2)

        output_dir = args.output_dir or "outputs"

        metrics = render_outputs(
            parsed_templates=[parsed_template] * len(valid_prospects),
            prospects=valid_prospects,
            output_dir=output_dir,
            export_format=args.format,
            combined_output_path=args.combined_output,
            dry_run=args.dry_run,
        )

        # -----------------------------
        # Dry run reporting
        # -----------------------------
        if args.dry_run:
            print("Dry run complete")
            print(
                f"Valid prospects: {len(valid_prospects)} | "
                f"Rendered: {metrics['rendered']} | "
                f"Skipped: {metrics['skipped']}"
            )
            sys.exit(0)

        print(
            f"Rendered {metrics['rendered']} emails "
            f"({metrics['skipped']} skipped)."
        )
        print(f"Output directory: {output_dir}")

        if metrics["rendered"] == 0:
            sys.exit(2)

        sys.exit(0)

    except (
        DataLoadError,
        ValidationError,
        TemplateError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


# -----------------------------
# Helpers
# -----------------------------

def _handle_preview(
    parsed_template,
    prospects,
    preview_index: int,
) -> None:
    index = preview_index - 1
    if index < 0 or index >= len(prospects):
        raise ValidationError(
            f"Preview index {preview_index} is out of range."
        )

    prospect = prospects[index]

    body = parsed_template.body
    for placeholder in parsed_template.placeholders:
        body = body.replace(
            f"{{{{{placeholder}}}}}",
            prospect.get(placeholder, ""),
        )

    if parsed_template.headers:
        headers = "\n".join(
            f"{k}: {v}" for k, v in parsed_template.headers.items()
        )
        print(headers + "\n\n" + body)
    else:
        print(body)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate personalized cold emails from a template and prospect data."
    )

    parser.add_argument(
        "--template",
        required=True,
        help="Path to the email template file.",
    )

    parser.add_argument(
        "--data",
        required=True,
        help="Path to prospect data file (.csv or .json).",
    )

    parser.add_argument(
        "--output-dir",
        help="Base output directory (default: ./outputs).",
    )

    parser.add_argument(
        "--format",
        default="txt",
        choices=["txt", "md", "html", "eml", "csv"],
        help="Output format.",
    )

    parser.add_argument(
        "--combined-output",
        help="Optional combined output file path.",
    )

    parser.add_argument(
        "--preview",
        type=int,
        help="Render a single prospect to stdout (1-based index).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without writing files.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print skipped prospects and warnings.",
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
