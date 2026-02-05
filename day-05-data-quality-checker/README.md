# Data Quality Checker (CLI)

A focused, production-style CLI tool for running explicit, configurable data quality checks against tabular datasets (CSV).

This is designed as an internal data reliability tool, not a data cleaning library and not an auto-fix system. The emphasis is on clarity, auditability, and predictable behavior.

## What this tool does

- Loads a CSV dataset
- Runs a curated set of data quality checks
- Applies config-driven severity policies
- Groups checks by category (structure, completeness, sanity, types)
- Compares results against a previous baseline

Emits:

- a human-readable report
-a machine-readable run summary for pipelines

## What this tool intentionally does NOT do

- Auto-fix data
- Guess intent
- Infer schema automatically
- Hide failures behind “health scores”

Every rule is explicit. Every failure is explainable.

## Supported check categories

### Structure

- Missing required columns

### Completeness

- Missing values (per column)
- Empty datasets

### Sanity

- Duplicate rows
- Unexpected row counts

### Types

- Mixed-type columns
- Invalid numeric coercions

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

This allows for customisation:
the same check can be acceptable in one dataset and fatal in another.

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

Every exclusion is deliberate and reviewable.

## Baseline comparison

Runs can be compared against a previous report to detect regressions.
- New failures
- Worsening metrics
- Health score drops

## Machine-readable run summary

Each run outputs a summary file:
```json
{
  "status": "fail",
  "health_score": 72,
  "regression": true,
  "failed_checks": 2
}
```

## Example usage
```bash
python -m src.cli data/sample.csv
```

List available checks:
```bash
python -m src.cli data/sample.csv --list-checks
```

Run with config:
```bash
python -m src.cli data/sample.csv --config config.json
```

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
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Design philosophy

- Explicit over clever
- Configuration over hard-coding
- Fail loudly, explain clearly
- No hidden state
- No auto-correction

This tool is meant to surface problems, not mask them.

## Limitations and future work

With more time, the next additions would be:
- Schema versioning
- Pluggable custom checks
- JSON/YAML schema validation
- Native Parquet support
- Historical trend storage
- CI exit codes per severity tier

All intentionally left out to keep the core tight and understandable.

## Dataset Health Score

This tool produces a dataset-level health score from 0 to 100.

The score is intended to give a fast, coarse signal for whether a dataset
is safe to use in downstream systems.

Scoring rules:

- Each warning reduces the score by 5 points
- Each failure reduces the score by 20 points
- The score is capped between 0 and 100

The exact weighting is intentionally simple and explainable.

## Strict Mode

By default, warnings do not fail the run.

When --strict is enabled, warnings are treated as failures and the tool
exits with a non-zero status code.

This mode is intended for:
- CI pipelines
- Data ingestion gates
- Pre-model-training checks

Example:
```bash
python cli.py data/sample_dirty.csv --config schema.json --strict
```
## Exit Codes

- 0 — all checks passed
- 1 — warnings present
- 2 — failures present (or strict mode violation)

## Baseline Comparison

The tool can compare the current run against a previous report to detect
quality regressions.

This comparison focuses on stable signals only:
- dataset health score
- number of warnings
- number of failures

Example:
```bash
python cli.py data/new.csv --baseline report_previous.json
```

If the dataset quality has regressed, the report will include a
baseline_comparison section and the console output will surface the change.

When used with --strict, regressions will cause the run to fail.

## Design philosophy

This tool is intentionally opinionated and minimal.

- **Checks declare facts, not policy**  
  Each check reports what it finds. Severity and enforcement are applied later via configuration.

- **Severity can only escalate**  
  Configuration may tighten standards over time, but cannot hide real failures.

- **Metadata travels with results**  
  Categories, column impact, and details are produced by checks themselves, not inferred downstream.

- **Deterministic and CI-friendly**  
  Given the same data and config, results are stable, machine-readable, and suitable for automation.

- **No silent coercion**  
  Input data is loaded conservatively to surface data quality issues rather than mask them.

