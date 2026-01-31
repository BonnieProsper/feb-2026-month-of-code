## Business Directory Normalizer

This is a small CLI tool that takes messy public business directory data (CSV or JSON) and produces a clean, normalized CSV suitable for downstream use (analysis, enrichment, lead generation, etc).

Public registries often publish data with inconsistent field names, categories, locations, and websites. This tool focuses on cleaning and standardizing that data in a simple, predictable way.

The goal is not perfect correctness, but a clear and reliable normalization pass that’s easy to reason about and easy to extend if needed.

### What the tool does

Given a CSV or JSON file containing business records, the tool:

- accepts inconsistent input keys (e.g. company, business_name, organization)
- normalizes core fields:
    - business name
    - category
    - location (city/region/country)
    - website URL
- handles missing or malformed values gracefully
- outputs a single clean CSV with a fixed schema and deterministic ordering

The output schema is always:

name,category,city,region,country,website

### What it does not do

This tool intentionally does not:
- scrape websites
- enrich data via external APIs
- perform fuzzy or ML-based matching
- validate addresses or geocode locations
- act as a general-purpose data pipeline

It is a single, well-scoped normalization step.

### Project structure

day-01-business-directory-aggregator/
  README.md
  src/
    main.py
    normalize.py
    file_io.py
  tests/
    test_normalization.py
  data/
    sample_raw.csv
    sample_raw.json
    sample_clean.csv

### How to run the tool

From the project root:

Normalize a CSV file
python src/main.py data/sample_raw.csv output.csv

Normalize a JSON file
python src/main.py data/sample_raw.json output.csv

The output will be written to output.csv.
On success, the tool produces no terminal output.

### Example
#### Input (CSV)
business_name,industry,location,website
Acme   Corp,Tech,"Berlin, Germany",acme.com
Pizza Palace,Restaurants,"Rome, Lazio, Italy",http://pizzapalace.it

#### Output (CSV)
name,category,city,region,country,website
Acme Corp,technology,Berlin,,Germany,https://acme.com
Pizza Palace,restaurant,Rome,Lazio,Italy,http://pizzapalace.it

### How normalization works 

- Names are trimmed and internal whitespace is collapsed.
- Categories are lowercased and lightly normalized using a small, explicit mapping.
- Locations prefer structured fields (city, region, country) and fall back to simple comma-based parsing if needed.
- Websites are cleaned conservatively:
  - schemes are added when missing
  - clearly invalid values are dropped

If a value can’t be confidently extracted, it is left empty.

### Running tests

Tests focus on core normalization behavior.

To run them:

pytest


They are intentionally minimal and designed to read like examples of expected behavior.

### Design decisions

- Flat structure with no frameworks to keep the code easy to follow.
- Normalization logic is isolated from I/O for testability.
- Input row order is preserved to avoid surprising behavior.
- Errors fail early and clearly rather than being silently ignored.

### Known limitations

- Category normalization is heuristic and incomplete by design.
- Location parsing is shallow and not suitable for precise geographic work.
- JSON input must be a list of objects.
- Output is always CSV.

These tradeoffs were made to keep the project well-scoped.

### What I’d do with more time

- Add optional sorting or filtering flags to the CLI.
- Expand category normalization using a configurable mapping.
- Add lightweight validation reporting (e.g counts of dropped websites).
- Support streaming large files instead of loading everything into memory.