"""
Broken Link Checker (CLI)

Features:
- Bounded crawl of a single domain
- Internal / external / anchor link classification
- Sync or async (aiohttp) link checking
- HEAD requests by default (optional fallback)
- CSV output sorted by severity
- Markdown summary report
- JSON machine-readable summary
- Graceful Ctrl+C handling
- CI-ready exit codes (--fail-on-broken)

Designed to be readable, maintainable, and production-quality.
"""

import argparse
import asyncio
import csv
import json
import signal
import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from urllib.parse import urlparse

from tqdm import tqdm
import aiohttp

from src.crawler import crawl_site
from src.checker import check_link
from src.async_checker import check_link_async


# =========================
# CLI
# =========================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Bounded broken link checker for a single domain"
    )

    parser.add_argument("base_url", help="Base URL to crawl")

    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--retries", type=int, default=1)

    parser.add_argument("--output", default="broken_links.csv")

    parser.add_argument(
        "--no-head",
        action="store_true",
        help="Disable HEAD requests (use GET only)",
    )

    parser.add_argument(
        "--async",
        dest="use_async",
        action="store_true",
        help="Use async checker (aiohttp) for faster runs",
    )

    parser.add_argument(
        "--fail-on-broken",
        action="store_true",
        help="Exit with non-zero code if broken links are found (CI-friendly)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print link status as they are checked",
    )

    return parser.parse_args()


# =========================
# Color helpers
# =========================

def green(t: str) -> str:
    return f"\033[92m{t}\033[0m"


def yellow(t: str) -> str:
    return f"\033[93m{t}\033[0m"


def red(t: str) -> str:
    return f"\033[91m{t}\033[0m"


# =========================
# Link classification
# =========================

def classify_link(base_url: str, link_url: str) -> str:
    """
    Classify link as:
    - anchor   (#fragment only)
    - internal (same domain or relative)
    - external (different domain)
    """
    if link_url.startswith("#"):
        return "anchor"

    base_netloc = urlparse(base_url).netloc
    link_netloc = urlparse(link_url).netloc

    if not link_netloc or link_netloc == base_netloc:
        return "internal"

    return "external"


# =========================
# Output helpers
# =========================

def severity_key(row):
    """
    Sort order (lower = worse):
    connection errors > timeouts > 5xx > 4xx > others
    """
    status = row[2]

    if status in ("timeout", "connection_error", "request_error"):
        return 0

    try:
        code = int(status)
        if 500 <= code <= 599:
            return 1
        if 400 <= code <= 499:
            return 2
    except ValueError:
        pass

    return 3


def write_csv(path: Path, rows):
    rows_sorted = sorted(rows, key=severity_key)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_page", "link_url", "status", "link_type"])
        writer.writerows(rows_sorted)


def write_json_summary(
    path: Path,
    base_url: str,
    base_status: str,
    pages_scanned: int,
    total_links: int,
    broken_rows,
):
    summary = {
        "base_url": base_url,
        "base_status": base_status,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "stats": {
            "pages_scanned": pages_scanned,
            "links_checked": total_links,
            "broken_links": len(broken_rows),
        },
        "severity_counts": {
            "timeouts": sum(1 for _, _, s, _ in broken_rows if s == "timeout"),
            "connection_errors": sum(1 for _, _, s, _ in broken_rows if s == "connection_error"),
            "5xx": sum(1 for _, _, s, _ in broken_rows if s.isdigit() and 500 <= int(s) <= 599),
            "4xx": sum(1 for _, _, s, _ in broken_rows if s.isdigit() and 400 <= int(s) <= 499),
        },
        "outputs": {
            "csv": str(path.with_suffix(".csv")),
            "markdown": str(path.with_suffix(".md")),
            "json": str(path.with_suffix(".json")),
        },
    }

    with path.with_suffix(".json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def write_markdown_report(
    path: Path,
    base_url: str,
    base_status: str,
    pages_scanned: int,
    total_links: int,
    broken_rows,
):
    md_path = path.with_suffix(".md")

    lines = [
        "# Broken Link Report",
        "",
        f"**Base URL:** {base_url}",
        f"**Base Status:** {base_status}",
        f"**Generated:** {datetime.utcnow().isoformat()}Z",
        "",
        "## Summary",
        f"- Pages scanned: {pages_scanned}",
        f"- Links checked: {total_links}",
        f"- Broken links: {len(broken_rows)}",
        "",
        "## Broken Links",
        "",
        "| Source Page | Link URL | Status | Type |",
        "|-------------|----------|--------|------|",
    ]

    for source, url, status, link_type in sorted(broken_rows, key=severity_key):
        lines.append(f"| {source} | {url} | {status} | {link_type} |")

    md_path.write_text("\n".join(lines), encoding="utf-8")


# =========================
# Main
# =========================

async def main():
    args = parse_args()
    broken_rows = []
    interrupted = False

    def handle_sigint(*_):
        nonlocal interrupted
        interrupted = True
        print(yellow("\nInterrupted — writing partial reports..."))

    signal.signal(signal.SIGINT, handle_sigint)

    # --- Base page check ---
    status, error = check_link(
        args.base_url,
        timeout=args.timeout,
        retries=args.retries,
        use_head=not args.no_head,
    )

    base_status = "ok"
    if error:
        base_status = error
        print(red(f"Base page error: {error}"))
        broken_rows.append((args.base_url, args.base_url, error, "base"))
    elif status is not None and status >= 400:
        base_status = str(status)
        print(red(f"Base page status: {status}"))
        broken_rows.append((args.base_url, args.base_url, str(status), "base"))
    else:
        print(green("Base page OK"))

    # --- Crawl ---
    pages_scanned, discovered_links = crawl_site(
        base_url=args.base_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
    )

    if not discovered_links:
        print(yellow("No links discovered during crawl."))

    # --- Link checking ---
    async def check_loop():
        if args.use_async:
            async with aiohttp.ClientSession() as session:
                for source, url, link_type in tqdm(discovered_links, desc="Checking links", unit="link"):
                    if interrupted:
                        break
                    if link_type == "anchor":
                        continue
                    status, error = await check_link_async(session, url, timeout=args.timeout, retries=args.retries, use_head=not args.no_head)
                    if error or (status and status >= 400):
                        broken_rows.append((source, url, error or str(status), link_type))
                        if args.verbose:
                            print(red(f"BROKEN {url} ({error or status})"))
                    elif args.verbose:
                        print(green(f"OK {url} ({status})"))
        else:
            for source, url, link_type in tqdm(discovered_links, desc="Checking links", unit="link"):
                if interrupted:
                    break
                if link_type == "anchor":
                    continue
                status, error = check_link(url, timeout=args.timeout, retries=args.retries, use_head=not args.no_head)
                if error or (status and status >= 400):
                    broken_rows.append((source, url, error or str(status), link_type))
                    if args.verbose:
                        print(red(f"BROKEN {url} ({error or status})"))
                elif args.verbose:
                    print(green(f"OK {url} ({status})"))

    await check_loop()

    # --- Reports ---
    output_path = Path(args.output)
    write_csv(output_path, broken_rows)
    write_markdown_report(output_path, args.base_url, base_status, pages_scanned, len(discovered_links), broken_rows)
    write_json_summary(output_path, args.base_url, base_status, pages_scanned, len(discovered_links), broken_rows)

    # --- Summary ---
    print("\nCrawl complete")
    print(f"Pages scanned: {pages_scanned}")
    print(f"Links checked: {len(discovered_links)}")
    print(f"Broken links found: {len(broken_rows)}")
    print(f"Reports written to: {output_path.resolve()}")
    print(green("No broken links found 🎉") if not broken_rows else red(f"Broken links found: {len(broken_rows)}"))

    if args.fail_on_broken and broken_rows:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
