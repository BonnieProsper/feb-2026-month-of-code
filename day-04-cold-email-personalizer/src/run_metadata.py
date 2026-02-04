import json
from pathlib import Path
from typing import List


def write_run_metadata(
    *,
    run_dir: Path,
    timestamp: str,
    template_hash: str,
    input_file: str,
    rendered_count: int,
    skipped_count: int,
    skipped_reasons: List[str],
) -> None:
    """
    Write run metadata to run.json inside the run directory.

    This file exists to support:
    - Auditing
    - Reproducibility
    - Debugging
    """
    payload = {
        "timestamp": timestamp,
        "template_hash": template_hash,
        "input_file": input_file,
        "rendered": rendered_count,
        "skipped": skipped_count,
        "skipped_reasons": skipped_reasons,
    }

    path = run_dir / "run.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
