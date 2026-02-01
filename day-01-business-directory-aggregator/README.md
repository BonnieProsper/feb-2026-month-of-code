## Business Directory Aggregator

A small, opinionated CLI tool for turning messy public business directory data into a clean, normalized CSV - with optional, fully modular enrichment.

Public registries often publish data with inconsistent field names, categories, locations, and websites. This tool focuses on producing a predictable, extensible baseline dataset that’s easy to reason about and easy to build on.

The emphasis is clarity and correctness over cleverness.

### What this tool does

Given a CSV or JSON file containing business records, the tool:

- accepts inconsistent input keys (e.g. company, business_name, organization)
- normalizes a core schema:
  - name
  - category
  - city/region/country
  - website
- handles missing or malformed values gracefully
- optionally deduplicates records
- optionally enriches records via a plugin system
- outputs a single clean CSV with a deterministic schema

The output schema automatically adapts to any enrichment plugins that are enabled.

### What it intentionally does not do

This project is deliberately scoped. It does not:
- scrape or geocode data by default
- perform ML-based matching
- act as a general-purpose ETL framework

It is meant to be a clean, inspectable normalization + enrichment step.
Scraping and geocoding are available only via explicitly enabled plugins.

### Project structure
```powershell
day-01-business-directory-aggregator/
  README.md
  src/
    main.py              # CLI + orchestration only
    file_io.py           # CSV/JSON streaming
    normalize.py         # normalization + dedup logic
    enrich/
      registry.py        # plugin discovery + loading
      plugins/           # drop-in enrichment plugins
  tests/
    test_normalization.py
  data/
    sample_raw.csv
    sample_raw.json
```

### Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

This project is intended to be run as a module, not as a script.

### How to run

From the project root (day-01-business-directory-aggregator):

#### List available enrichment plugins
```bash
python -m src.main --list-plugins
```

#### Normalize a CSV file
```bash
python -m src.main data/sample_raw.csv output.csv
```

#### Normalize with enrichment and deduplication
```bash
python -m src.main data/sample_raw.csv output.csv \
  --deduplicate \
  --enable-plugin scrape_title \
  --enable-plugin geocode
```

(On Windows/PowerShell, run this on a single line.)

#### Dry run (inspect schema without writing output)
```bash
python -m src.main data/sample_raw.csv output.csv --dry-run
```

### Enrichment plugins

Enrichment is fully modular.
- Plugins live in src/enrich/plugins/
- Each plugin exposes:
  - name: str
  - enrich(row) -> dict | None
- Any new fields returned by plugins are automatically added to the output CSV

Plugins can be enabled selectively via --enable-plugin.

### Output schema

The following columns are always present:

name, category, city, region, country, website

Any additional columns come from enabled enrichment plugins

When enrichment plugins are enabled, additional columns are appended automatically:

name, category, city, region, country, website, lat, lon, website_title

### Tests

Tests focus on core normalization behavior.

To run them:
```bash 
pytest
```

### Design decisions

- Clear separation between I/O, normalization, enrichment, and orchestration
- No framework dependencies
- Defensive plugin boundaries (one bad plugin can’t break the pipeline)
- Dynamic schema generation without hardcoding enrichment fields
- Explicit CLI behavior over “magic” defaults

### Known limitations

- Category normalization is heuristic and intentionally small
- Location parsing is shallow and not address-accurate
- JSON input must be a list of objects
- Output is always CSV
- Enrichment plugins are trusted code (not sandboxed)

These tradeoffs are intentional to keep the project focused.

### What I’d do next

- Plugin-level configuration flags
- Optional concurrency for slow enrichments
- Lightweight data quality scoring
- Streaming output for very large files