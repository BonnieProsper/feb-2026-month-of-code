# Cold Email Personalizer (CLI)

A focused, production‑style command‑line tool for generating high‑quality, personalized cold emails from structured data and clean templates.

This project is intentionally narrow: no AI text generation, no CRM bloat, no external APIs. The goal is deterministic, inspectable personalization - the kind of tool you could confidently wire into a real outbound workflow.

---

## What this tool does

* Loads recipient and company data from CSV or JSON
* Validates required fields and schema consistency
* Applies a lightweight template engine with explicit placeholders
* Renders one email per recipient, predictably and safely
* Outputs ready‑to‑send text files or stdout

---

## What this tool deliberately does *not* do

*  No LLMs or prompt chaining
*  No email sending or tracking
*  No implicit magic or hidden transformations

If an email looks wrong, you can trace exactly why.

---

## Example

### Template

```text
Hi {{first_name}},

I came across {{company_name}} and noticed you're working on {{product_area}}.

We've helped teams like Manning Analytics reduce {{pain_point}} by {{outcome_metric}}.

Worth a quick chat?

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

---

## CLI usage

```bash
cold-email render \
  --template templates/intro.txt \
  --data data/prospects.csv \
  --out out/
```

---

## Architecture

```
src/
    cli.py          # Argument parsing and command dispatch
    loader.py       # CSV/JSON loading
    validation.py   # Schema + placeholder validation
    template_engine.py     # Template parsing rules
    renderer.py     # Deterministic render engine

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

## Design Decisions

- **Strict placeholders**  
  Templates fail fast if required fields are missing, preventing silent personalization errors.

- **Timestamped output runs**  
  Each execution writes to a unique directory to avoid overwriting previous campaigns and to support auditability.

- **CSV / JSON only**  
  Common, explicit formats keep the tool predictable and easy to integrate into existing workflows.

- **Fail-fast validation**  
  Data issues are surfaced early with clear errors to avoid generating incorrect outreach.
