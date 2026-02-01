"""
Main entry point for the Business Directory Aggregator.

Responsibilities:
- Stream CSV/JSON input
- Normalize raw records into a clean canonical schema
- Optionally deduplicate records
- Apply enrichment plugins (auto-discovered + configurable)
- Dynamically adapt output schema based on enrichments
- Emit a clean CSV plus optional quality report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Set, Mapping, Optional

from src.file_io import read_csv_stream, read_json_stream, write_csv
from src.normalize import normalize_record, CATEGORY_MAP, is_duplicate
from src.enrich.registry import load_plugins, discover_plugins


# Core schema — guaranteed columns in every output file
CORE_COLUMNS = ["name", "category", "city", "region", "country", "website"]


def _load_category_map(path: Path) -> None:
    """
    Extend the built-in CATEGORY_MAP from an external JSON file.
    External mappings override internal ones.
    """
    if not path.exists():
        raise SystemExit(f"Category map file does not exist: {path}")

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise SystemExit(f"Failed to read category map: {exc}")

    if not isinstance(data, dict):
        raise SystemExit("Category map must be a JSON object")

    CATEGORY_MAP.update({str(k).lower(): str(v).lower() for k, v in data.items()})


def _iter_rows(input_path: Path):
    """Yield raw rows from CSV or JSON input."""
    suffix = input_path.suffix.lower()

    if suffix == ".csv":
        return read_csv_stream(str(input_path))
    if suffix == ".json":
        return read_json_stream(str(input_path))

    raise SystemExit("Input file must be .csv or .json")


def _apply_plugins_sequential(
    *,
    row: Dict[str, str],
    plugins: Iterable[object],
    timing: Dict[str, float],
    failures: Counter,
    enrichment_columns: Set[str],
) -> None:
    """
    Apply enrichment plugins sequentially to a single row.

    Plugins are expected to expose:
      - name: str
      - enrich(row: Dict[str, str]) -> Optional[Mapping[str, str]]

    This function is intentionally defensive: plugin output is validated
    at runtime so one bad plugin cannot corrupt the pipeline.
    """
    for plugin in plugins:
        enrich_fn = getattr(plugin, "enrich", None)
        if not callable(enrich_fn):
            continue

        plugin_name = getattr(plugin, "name", "<unknown>")

        start = time.perf_counter()
        try:
            result = enrich_fn(row)
        except Exception:
            failures[plugin_name] += 1
            continue
        finally:
            timing[plugin_name] += time.perf_counter() - start

        if not result:
            continue

        if not isinstance(result, Mapping):
            failures[plugin_name] += 1
            continue

        # Narrowed type: Mapping[str, str]
        clean: Dict[str, str] = {
            str(k): str(v)
            for k, v in result.items()
            if v is not None
        }

        if not clean:
            continue

        row.update(clean)
        enrichment_columns.update(clean.keys())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize and enrich business directory datasets."
    )

    # Positional arguments
    parser.add_argument("input_file", nargs="?", help="Input CSV or JSON file")
    parser.add_argument("output_file", nargs="?", help="Output CSV file")

    # Core processing options
    parser.add_argument("--min-fields", type=int, default=0)
    parser.add_argument("--deduplicate", action="store_true")
    parser.add_argument("--sort", choices=["name"])

    # Enrichment system
    parser.add_argument(
        "--enable-plugin",
        action="append",
        default=[],
        help="Enable enrichment plugin by name (repeatable)",
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List available enrichment plugins and exit",
    )

    # Execution behavior
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process input and show output schema without writing CSV",
    )

    # Optional extensions
    parser.add_argument("--category-map", help="Path to JSON category mapping")
    parser.add_argument("--report", help="Write a JSON quality report")

    args = parser.parse_args()

    # Plugin discovery mode
    if args.list_plugins:
        plugins = discover_plugins()
        print("Available enrichment plugins:")
        for name in sorted(plugins):
            print(f"- {name}")
        sys.exit(0)

    if not args.input_file or not args.output_file:
        parser.error("input_file and output_file are required unless --list-plugins")

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    if not input_path.exists():
        raise SystemExit(f"Input file does not exist: {input_path}")

    if args.category_map:
        _load_category_map(Path(args.category_map))

    plugins = load_plugins(args.enable_plugin)

    unknown = set(args.enable_plugin) - set(plugins.keys())
    if unknown:
        print(f"Warning: unknown plugins ignored: {', '.join(sorted(unknown))}")

    rows = _iter_rows(input_path)

    normalized_rows: List[Dict[str, str]] = []
    enrichment_columns: Set[str] = set()
    skipped = Counter()

    plugin_timing: Dict[str, float] = defaultdict(float)
    plugin_failures = Counter()

    for raw in rows:
        if not isinstance(raw, dict):
            skipped["invalid_row"] += 1
            continue

        row = normalize_record(raw)

        filled = sum(bool(row.get(col)) for col in CORE_COLUMNS)
        if filled < args.min_fields:
            skipped["min_fields"] += 1
            continue

        if args.deduplicate and is_duplicate(normalized_rows, row):
            skipped["duplicate"] += 1
            continue

        _apply_plugins_sequential(
            row=row,
            plugins=plugins.values(),
            timing=plugin_timing,
            failures=plugin_failures,
            enrichment_columns=enrichment_columns,
        )

        normalized_rows.append(row)

    if args.sort == "name":
        normalized_rows.sort(key=lambda r: r.get("name", "").lower())

    all_columns = CORE_COLUMNS + sorted(enrichment_columns)

    if args.dry_run:
        print("Dry run complete.")
        print(f"Rows that would be written: {len(normalized_rows)}")
        print("Output columns:")
        for col in all_columns:
            print(f"- {col}")
        sys.exit(0)

    write_csv(
        str(output_path),
        normalized_rows,
        fieldnames=all_columns,
    )

    print(f"Normalized {len(normalized_rows)} rows → {output_path}")

    if skipped:
        print("Skipped rows:")
        for reason, count in skipped.items():
            print(f"  {reason}: {count}")

    if plugin_timing:
        print("Plugin execution time (seconds):")
        for name, seconds in plugin_timing.items():
            print(f"  {name}: {seconds:.3f}")

    if plugin_failures:
        print("Plugin failures:")
        for name, count in plugin_failures.items():
            print(f"  {name}: {count}")

    if args.report:
        report_path = Path(args.report)
        report = {
            "rows_written": len(normalized_rows),
            "skipped": dict(skipped),
            "plugins_enabled": list(plugins.keys()),
            "plugin_timing_seconds": dict(plugin_timing),
            "plugin_failures": dict(plugin_failures),
            "output_columns": all_columns,
        }

        try:
            with report_path.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"Report written to {report_path}")
        except Exception as exc:
            print(f"Failed to write report: {exc}")


if __name__ == "__main__":
    main()
