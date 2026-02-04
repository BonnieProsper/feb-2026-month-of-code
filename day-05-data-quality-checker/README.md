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