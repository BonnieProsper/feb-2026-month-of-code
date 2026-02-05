# Data Quality Checker (CLI)

A focused, production-style CLI tool for running explicit, configurable data quality checks against tabular datasets (CSV).

This is designed as an internal data reliability tool, not a data cleaning library and not an auto-fix system. The emphasis is on clarity, auditability, and predictable behavior.

## What this tool does

- Loads a CSV dataset
- Runs a curated set of data quality checks
- Applies config-driven severity policies
- Groups checks by category (structure, completeness, sanity, types)
- Optionally compares results against a previous baseline

Emits:

- a human-readable console summary
- a detailed JSON report (report.json)
- a machine-readable run summary for pipelines (run_summary.json)

## What this tool intentionally does NOT do

- Auto-fix data
- Guess intent
- Infer schema automatically
- Hide failures behind abstract scores

Every rule is explicit. Every failure is explainable.

## Supported check categories

### Structure

- Missing required columns
- Unexpected columns (when a required schema is provided)

### Completeness

- Missing values (per column)
- Empty datasets/rows

### Sanity

- Duplicate rows
- Constant (single-value) columns

### Types

- Mixed-type columns
- Numeric-like strings in non-numeric columns

Each check is deterministic, side-effect free and independently configurable

## Config-driven severity 

Severity is policy, not logic.

Example:
```json
{
  "severity": {
    "missing_values": "warn",
    "duplicate_rows": "fail",
    "mixed_types": "warn"
  }
}
```

Valid severities:
- pass
- warn
- fail

This allows the same check to be acceptable in one dataset and fatal in another without changing code.

## Column allowlists/ignore rules

Real datasets contain junk. This tool makes that explicit.
```json
{
  "ignore_columns": ["free_text_notes"],
  "ignore": {
    "missing_values": ["comments"]
  }
}
```
- ignore_columns applies globally
- ignore applies per check

Every exclusion is deliberate and reviewable.

## Baseline comparison

Runs can be compared against a previous report to detect regressions.
- New failures
- Worsening metrics
- Dataset health score drops

This is intended for CI pipelines and ingestion gates.

## Machine-readable run summary

Each run outputs a summary file:
```json
{
  "status": "fail",
  "exit_code": 2,
  "health_score": 40,
  "checks": {
    "total": 6,
    "passed": 3,
    "warned": 0,
    "failed": 3
  }
}
```

## Example usage

Run checks against a dataset:
```bash
python -m src.cli data/sample_dirty.csv
```

List available checks and categories:
```bash
python -m src.cli data/sample_dirty.csv --list-checks
```

Run with a config file:
```bash
python -m src.cli data/sample_dirty.csv --config config/example.json
```

Run only a subset of categories:
```bash
python -m src.cli data/sample_dirty.csv --only-category completeness --only-category types
```

Run in strict mode (warnings fail the run):
```bash
python -m src.cli data/sample_dirty.csv --strict
```
## Baseline comparison example

Generate a baseline:
```bash
python -m src.cli data/sample_clean.csv
```

Move the generated report:
```bash
mkdir reports
mv report.json reports/previous.json
```

Compare a new run against the baseline:
```bash
python -m src.cli data/sample_dirty.csv --baseline reports/previous.json
```

If quality regresses, the report and console output will surface the change.

## Exit codes

- 0 — all checks passed
- 1 — warnings present
- 2 — failures present (or strict-mode violations)

Project structure
```text
src/
  cli.py
  report.py
  loader.py
  schema.py
  checks/
    structure.py
    completeness.py
    sanity.py
    types.py
tests/
data/
config/
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Dataset health score

The tool produces a dataset-level health score from 0 to 100.

Scoring rules:
- Each warning: −5 points
- Each failure: −20 points
- Score is capped between 0 and 100

The score is intended as a coarse safety signal, not a replacement for inspection.

## Design philosophy

- Explicit over clever
- Configuration over hard-coding
- Checks declare facts, not policy
- Severity can only escalate, never hide issues
- Deterministic and CI-friendly
- No silent coercion or auto-correction

This tool is meant to surface problems, not mask them.

## Limitations and future work

With more time, the next additions would include:
- Schema versioning
- Pluggable custom checks
- JSON/YAML schema validation
- Native Parquet support
- Historical trend storage
- CI policies per severity tier

These are intentionally left out to keep the core tight, readable, and auditable.