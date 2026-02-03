import re
from pathlib import Path
from typing import List, Dict


def render_outputs(
    rendered_emails: List[str],
    prospects: List[Dict[str, str]],
    output_dir: str,
    combined_output_path: str | None = None,
) -> None:
    """
    Write rendered emails to disk.

    One file is written per prospect. Optionally, a combined
    output file is also generated.
    """
    if len(rendered_emails) != len(prospects):
        raise ValueError("Rendered emails and prospects count do not match.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    used_filenames: set[str] = set()

    for index, (email, prospect) in enumerate(
        zip(rendered_emails, prospects), start=1
    ):
        base_name = _build_base_filename(prospect, index)
        filename = _deduplicate_filename(base_name, used_filenames)
        used_filenames.add(filename)

        file_path = output_path / f"{filename}.txt"
        file_path.write_text(email, encoding="utf-8")

    if combined_output_path:
        _write_combined_output(
            rendered_emails,
            prospects,
            Path(combined_output_path),
        )


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


def _write_combined_output(
    rendered_emails: List[str],
    prospects: List[Dict[str, str]],
    path: Path,
) -> None:
    sections: List[str] = []

    for index, (email, prospect) in enumerate(
        zip(rendered_emails, prospects), start=1
    ):
        header = _describe_prospect(prospect, index)
        sections.append(
            f"----- {header} -----\n{email}"
        )

    content = "\n\n".join(sections)
    path.write_text(content, encoding="utf-8")


def _describe_prospect(prospect: Dict[str, str], index: int) -> str:
    if prospect.get("company"):
        return f'prospect #{index} (company={prospect["company"]})'
    return f"prospect #{index}"
