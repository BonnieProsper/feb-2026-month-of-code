# Cold Email Personalizer (CLI)

A focused, production-style command-line tool for generating high-quality, personalized cold emails from structured data and deterministic templates.

This project is intentionally narrow in scope. It avoids AI text generation, CRM complexity, and external services in favor of correctness, transparency, and predictable behavior — the kind of tool you could safely wire into a real outbound workflow.

---

## What this tool does

- Loads prospect data from CSV or JSON
- Validates required fields and schema consistency
- Parses templates with explicit placeholders and optional headers
- Renders one email per valid prospect, deterministically
- Writes outputs to timestamped run directories
- Supports previewing, dry-runs, and combined outputs

---

## What this tool deliberately does *not* do

- No LLMs or prompt chaining
- No email sending, tracking, or analytics
- No implicit defaults or hidden transformations

If an email looks wrong, you can trace exactly why.

---

## Example

### Template

```text
Hi {{first_name}},

I noticed {{company}} is working on {{product_area}}.

We've helped teams reduce {{pain_point}} by {{outcome_metric}}.

Would you be open to a short conversation?

- {{sender_name}}
```

### Input data (CSV)

```csv
first_name,company_name,product_area,pain_point,outcome_metric,sender_name
Alex,Manning Analytics,data reliability,pipeline failures,37%,Bronson
```

### Output

```text
Hi Alex,

I came across Manning Analytics and noticed you're working on data reliability.

We've helped teams like Manning Analytics reduce pipeline failures by 37%.

Worth a quick chat?

- Bronson
```

## CLI usage

Render emails to disk:
```bash
python -m src.cli \
  --template data/sample_template.txt \
  --data data/sample_prospects.csv \
  --output-dir outputs \
  --format txt
```

Preview a single prospect (no files written):
```bash
python -m src.cli \
  --template data/sample_template.txt \
  --data data/sample_prospects.csv \
  --preview 1
```

Dry run (validate + simulate output):
```bash
python -m src.cli \
  --template data/sample_template.txt \
  --data data/sample_prospects.csv \
  --dry-run
```

Write all rendered emails to a combined file:
```bash
python -m src.cli \
  --template data/sample_template.txt \
  --data data/sample_prospects.csv \
  --combined-output outputs/all_emails.txt
```

## Output structure

Each run writes to a timestamped directory:
```text
outputs/
  2026-02-04_09-18-42/
    alex_manning.txt
    jordan_manning.txt
    run_metadata.json
```

This prevents accidental overwrites and supports auditability.

---

## Architecture

```
src/
  cli.py             # Argument parsing and orchestration
  loader.py          # CSV / JSON loading
  validation.py      # Schema + placeholder validation
  template_engine.py # Template parsing rules
  renderer.py        # Deterministic render engine
  run_metadata.py    # Per-run metadata logging
  types.py           # Shared domain types

tests/
```

Each module has a single responsibility and is testable in isolation.

---

## Design principles

* **Determinism over cleverness**
* **Fail fast on bad data**
* **Readable > extensible**
* **Explicit rules beat heuristics**

---

## Running tests

```bash
pytest
```

Type checking is clean under Pylance/Pyright.

## Limitations and next steps

This tool focuses on correctness and reliability, not delivery. Features intentionally left out to preserve single day scope include:

- Email sending (SMTP / SES / SendGrid)
- Campaign-level configuration files
- Subject-line variants or A/B testing
- CRM or analytics integration

These can be layered on without changing the core rendering or validation logic.