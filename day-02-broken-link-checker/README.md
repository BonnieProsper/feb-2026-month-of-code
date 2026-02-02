# Broken Link Checker (CLI)

A focused, production-style CLI tool to crawl a single website and report broken links in a safe, bounded, and predictable way.

This is a **diagnostic crawler**, not a full SEO platform. The goal is correctness, transparency, and engineering discipline rather than aggressive crawling or ranking metrics.

---

## What this tool does

- Crawls a website starting from a base URL
- Discovers and checks links found in HTML pages
- Reports broken links with clear context and severity
- Produces machine-readable and human-readable reports
- Can be safely used locally, in CI, or against production sites

---

## Features

### Crawling
- Crawl **a single domain** starting from a base URL
- **Exact hostname matching** for internal pages  
  (subdomains are treated as external)
- Bounded traversal:
  - `--max-depth` limits link hops
  - `--max-pages` caps total pages fetched
- Tracks visited URLs to prevent infinite loops

### Link checking
- Detects:
  - HTTP 4xx and 5xx responses
  - Timeouts and connection failures
- Optional **HEAD → GET fallback** for efficiency
- Retries transient failures (timeouts, 5xx)

### Performance
- **Optional async link checking** using `aiohttp`
  - Enabled with `--async`
  - Significant speed-ups on large sites
- Crawl remains synchronous by design (see Design Notes)

### Reporting
- **CSV report** (sorted by severity)
- **Markdown report** for human review
- **JSON summary** for automation/CI
- Broken links include:
  - Source page
  - Link URL
  - Failure reason
  - Link type (internal / external / anchor)

### UX & safety
- Progress bars for long runs
- Graceful Ctrl+C handling (partial reports are still written)
- Base page status is checked and reported
- CI-friendly mode with `--fail-on-broken`

---

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Optional dependency (only needed for async checking):
pip install aiohttp
```

## Usage
Basic usage:

```bash
python -m src.main https://example.com
```
With limits and output control:

```bash
python -m src.main https://example.com \
  --max-depth 2 \
  --max-pages 100 \
  --timeout 5 \
  --output broken_links.csv
```
Enable async checking and CI mode:

```bash
python -m src.main https://example.com \
  --async \
  --fail-on-broken
```
## CLI Arguments
- base_url (required) – starting URL
- --max-depth – maximum link hops (default: 2)
- --max-pages – maximum pages to crawl (default: 100)
- --timeout – request timeout in seconds (default: 5)
- --retries – retry count for transient failures (default: 1)
- --output – base output path (default: broken_links.csv)
- --no-head – disable HEAD requests
- --async – enable async link checking
- --fail-on-broken – exit non-zero if broken links are found
- --verbose – print broken links as they are detected

Example terminal output
````text
Base page status: ok
Checking links: 100%|██████████| 87/87 [00:01<00:00, 64.2 link/s]

Crawl complete
Broken links: 4
Report written to: /path/to/broken_links.csv
No broken links found 🎉
``` 

## Output formats
#### CSV (sorted by severity)
```bash
source_page,link_url,status,link_type
https://example.com/,https://example.com/old-page/,404,internal
https://example.com/about/,https://example.com/api/,timeout,external
``` 

Severity order:
- Timeouts / connection errors
- 5xx responses
- 4xx responses
- Other errors

Markdown: Human-readable report suitable for sharing or review.

JSON: Structured summary intended for CI/automation.

## Design notes
#### Why crawling is synchronous
Crawling is stateful and safety-critical (depth limits, domain rules, visit tracking). A synchronous crawl keeps behavior predictable and easy to reason about.

#### Why link checking can be async
Link checks are independent, I/O-bound operations. Making them optionally async provides large performance gains without complicating crawl logic.

#### Why subdomains are external
Treating subdomains as external avoids accidental cross-site crawling and keeps scope explicit. This can be relaxed in the future if needed.

## Known limitations
- Does not execute JavaScript
- Does not parse robots.txt or sitemaps
- Query parameters are not canonicalized
- Crawl itself is intentionally synchronous

These are deliberate tradeoffs to keep the tool safe, auditable, and predictable.

## Possible future improvements
- Async crawling (with strict concurrency limits)
- Optional subdomain inclusion
- Sitemap-based crawl bootstrapping
- Canonical URL normalization
- GitHub Actions example using --fail-on-broken

