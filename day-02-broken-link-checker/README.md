# Broken Link Checker (CLI)

A small, focused CLI tool that crawls a single website and reports broken internal links.

This is a bounded diagnostic tool, not a full SEO crawler. It is designed to be predictable, easy to reason about, and safe to run against real sites.

---

## What this tool does

- Crawls a single domain starting from a base URL
- Follows **internal links only** (same hostname)
- Uses a depth limit and page cap to bound crawling
- Checks discovered links for:
  - HTTP 4xx and 5xx responses
  - timeouts and request failures
- Outputs:
  - a concise terminal summary
  - a CSV report of broken links with source pages

---

## What this tool deliberately does *not* do

This project is intentionally scoped. It does **not** include:

- JavaScript rendering
- sitemap or robots.txt parsing
- external link checking
- parallel or asynchronous requests
- retries or backoff logic
- SEO scoring or recommendations

These omissions are deliberate to keep behavior predictable and the code easy to audit.

---

## Crawl boundaries and behavior

Crawling is bounded by three mechanisms:

1. **Domain restriction**  
   Only URLs with the exact same hostname as the base URL are considered internal.  
   Subdomains (e.g. `blog.example.com`) are treated as external and ignored.

2. **Depth limit**  
   Limits how many link hops away from the base page the crawler will go.

3. **Maximum page count**  
   Hard cap on how many pages will be fetched.

The crawler also tracks visited URLs to avoid infinite loops.

---

## Installation

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Dependencies are intentionally minimal.

## Usage
```bash
python -m src.main https://example.com \
  --max-depth 2 \
  --max-pages 100 \
  --output broken_links.csv
```

## Arguments

- base_url (required): starting point for the crawl
- --max-depth: maximum crawl depth (default: 2)
- --max-pages: maximum pages to scan (default: 100)
- --output: CSV output path (default: broken_links.csv)

## Example output

Terminal:

```text
Crawl complete
Pages scanned: 12
Links checked: 87
Broken links found: 4
Report written to: /path/to/broken_links.csv
```

CSV (broken_links.csv):

```text
source_page,link_url,status
https://example.com/,https://example.com/old-page/,404
https://example.com/about/,https://example.com/contact/,timeout
```

## Known limitations

- Pages that fail to load are skipped silently during crawling
- HTTP redirects are followed but not explicitly reported
- Query parameters are not canonicalized
- HEAD requests are not used (some servers mis-handle them)

## What I would improve with more time

- Optional retry logic for transient network failures
- Progress indicator for long crawls
- Configurable inclusion of subdomains
- Smarter URL canonicalization
- Optional sorting of CSV output by severity