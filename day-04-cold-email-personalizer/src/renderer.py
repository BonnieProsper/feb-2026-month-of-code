import re
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, TypedDict, Literal

from src.types import ParsedTemplate
from src.run_metadata import write_run_metadata

ExportFormat = Literal["txt", "md", "html", "eml", "csv"]


class RenderMetrics(TypedDict):
    rendered: int
    skipped: int


class RenderedProspect(TypedDict):
    content: str
    prospect: Dict[str, str]
    filename: str


def render_outputs(
    parsed_templates: List[ParsedTemplate],
    prospects: List[Dict[str, str]],
    output_dir: str,
    export_format: ExportFormat = "txt",
    combined_output_path: str | None = None,
    dry_run: bool = False,
) -> RenderMetrics:
    """
    Render parsed templates with prospect data and write outputs.

    Supports:
    - Timestamped run directories
    - Deterministic ordering
    - Dry-run mode
    - Partial success
    - Multiple export formats
    """
    if len(parsed_templates) != len(prospects):
        raise ValueError("Templates and prospects count do not match.")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = Path(output_dir) / timestamp

    if not dry_run:
        run_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(
        zip(parsed_templates, prospects),
        key=lambda p: (p[1].get("company", ""), p[1].get("first_name", "")),
    )

    used_filenames: set[str] = set()
    rendered_count = 0
    skipped_count = 0
    skipped_reasons: List[str] = []

    rendered_prospects: List[RenderedProspect] = []

    for index, (parsed, prospect) in enumerate(ordered, start=1):
        try:
            base_name = _build_base_filename(prospect, index)
            filename = _deduplicate_filename(base_name, used_filenames)
            used_filenames.add(filename)

            content = _render_parsed_template(parsed, prospect)

            if not dry_run:
                _write_file(
                    content=content,
                    path=run_dir / f"{filename}.{export_format}",
                    export_format=export_format,
                    prospect=prospect,
                )

            rendered_prospects.append(
                {
                    "content": content,
                    "prospect": prospect,
                    "filename": filename,
                }
            )
            rendered_count += 1

        except Exception as exc:
            skipped_count += 1
            skipped_reasons.append(
                f"{_describe_prospect(prospect, index)} skipped: {exc}"
            )

    if combined_output_path and not dry_run:
        combined_path = Path(combined_output_path)
        if combined_path.is_dir():
            combined_path = combined_path / f"combined.{export_format}"
        _write_combined_output(rendered_prospects, combined_path)

    if not dry_run:
        write_run_metadata(
            run_dir=run_dir,
            timestamp=timestamp,
            template_hash=_hash_template_contents(parsed_templates),
            input_file="unknown",
            rendered_count=rendered_count,
            skipped_count=skipped_count,
            skipped_reasons=skipped_reasons,
        )

    return {
        "rendered": rendered_count,
        "skipped": skipped_count,
    }


# ------------------------------
# Helpers
# ------------------------------

def _render_parsed_template(parsed: ParsedTemplate, context: Dict[str, str]) -> str:
    body = parsed.body
    for placeholder in parsed.placeholders:
        body = body.replace(f"{{{{{placeholder}}}}}", context.get(placeholder, ""))

    if parsed.headers:
        headers = "\n".join(f"{k}: {v}" for k, v in parsed.headers.items())
        return f"{headers}\n\n{body}"

    return body


def _write_file(
    *,
    content: str,
    path: Path,
    export_format: ExportFormat,
    prospect: Dict[str, str],
) -> None:
    if export_format == "csv":
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["content"])
            writer.writerow([content])
        return

    path.write_text(content, encoding="utf-8")


def _write_combined_output(
    rendered_prospects: List[RenderedProspect],
    path: Path,
) -> None:
    sections: List[str] = []

    for index, rp in enumerate(rendered_prospects, start=1):
        header = _describe_prospect(rp["prospect"], index)
        sections.append(f"----- {header} -----\n{rp['content']}")

    path.write_text("\n\n".join(sections), encoding="utf-8")


def _build_base_filename(prospect: Dict[str, str], index: int) -> str:
    if prospect.get("first_name") and prospect.get("company"):
        raw = f'{prospect["first_name"]}_{prospect["company"]}'
    elif prospect.get("company"):
        raw = prospect["company"]
    else:
        raw = f"prospect_{index}"

    return _normalize_filename(raw)


def _normalize_filename(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def _deduplicate_filename(base: str, used: set[str]) -> str:
    if base not in used:
        return base

    counter = 2
    while f"{base}_{counter}" in used:
        counter += 1

    return f"{base}_{counter}"


def _describe_prospect(prospect: Dict[str, str], index: int) -> str:
    if prospect.get("company"):
        return f'prospect #{index} (company={prospect["company"]})'
    return f"prospect #{index}"


def _hash_template_contents(parsed_templates: List[ParsedTemplate]) -> str:
    combined = "".join(t.body for t in parsed_templates)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
