# Broken Link Checker (CLI)

A focused, professional CLI tool to crawl a single website and report broken internal links.

This is a **diagnostic, bounded crawler**, not a full SEO tool. It emphasizes predictable behavior, safety, and transparency for real-world use.

---

## Features

- Crawl a **single domain** starting from a base URL
- Follow **internal links only** (exact hostname match; subdomains ignored)
- Configurable crawl limits:
  - `--max-depth` – maximum link hops
  - `--max-pages` – maximum pages fetched
- **Link checking** for:
  - HTTP 4xx / 5xx errors
  - Timeouts and request failures
- **Enhanced reliability**
  - Retry transient errors (timeouts, 5xx)
  - Configurable request timeout
- **Progress reporting** for long crawls
- **CSV output**, optionally sorted by severity
- Graceful handling of **Ctrl+C** to save partial results

---

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
Dependencies are minimal: requests and beautifulsoup4.
```

Usage
```bash
python -m src.main https://example.com \
  --max-depth 2 \
  --max-pages 100 \
  --timeout 5 \
  --output broken_links.csv
```

## Arguments:

- base_url (required): starting URL
- --max-depth: max link hops (default 2)
- --max-pages: max pages to scan (default 100)
- --timeout: HTTP request timeout in seconds (default 5)
- --output: CSV output path (default broken_links.csv)

## Example Terminal Output
```text
[Page 1/100] Crawling: https://example.com/
[Page 2/100] Crawling: https://example.com/about/
Crawl complete
Pages scanned: 12
Links checked: 87
Broken links found: 4
Report written to: /path/to/broken_links.csv
```

## Example CSV Output
```text
source_page,link_url,status
https://example.com/,https://example.com/old-page/,404
https://example.com/about/,https://example.com/contact/,timeout
CSV is sorted by severity: timeouts → 5xx → 4xx.
```

## Crawl Boundaries
- Domain restriction: only exact hostname matches are followed. Subdomains are ignored.
- Depth limit: limits link hops.
- Page limit: ensures the crawl is bounded.
- Visited tracking: prevents infinite loops.

## Known Limitations

- Does not render JavaScript
- Does not parse sitemap/robots.txt
- External links are ignored
- HEAD requests are not used
- Query parameters are not canonicalized

## Design Decisions

- Predictable behavior: limited depth and page caps, exact hostname matching
- User feedback: progress reporting for long crawls
- Reliability: retry on transient network errors
- Professional output: CSV sorted by severity, clear terminal summary
- Safety: avoids external links and JS execution

This tool prioritizes clarity, reliability, and auditability over brute-force crawling or SEO metrics.

## Possible Future Improvements

- Parallel/asynchronous crawling for speed
- Optional subdomain inclusion
- More advanced canonicalization of URLs
- Configurable CSV sorting options
- Integration with CI/CD to check live websites automatically