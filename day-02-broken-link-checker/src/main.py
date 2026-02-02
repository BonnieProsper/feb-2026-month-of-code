import argparse
import csv
import json
import signal
import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from urllib.parse import urlparse

from tqdm import tqdm

from src.crawler import crawl_site
from src.checker import check_link


# ---------- CLI ----------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Bounded broken link checker for a single domain"
    )

    parser.add_argument("base_url", help="Base URL to crawl")

    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--output", default="broken_links.csv")

    parser.add_argument(
        "--fail-on-broken",
        action="store_true",
        help="Exit with non-zero status if broken links are found (CI-friendly)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print link status as they are checked",
    )

    return parser.parse_args()


# ---------- Output helpers ----------

def classify_link(base_url: str, link_url: str) -> str:
    """
    Classify link type for reporting.
    """
    if link_url.startswith("#"):
        return "anchor"

    base_netloc = urlparse(base_url).netloc
    link_netloc = urlparse(link_url).netloc

    if not link_netloc or link_netloc == base_netloc:
        return "internal"

    return "external"


def write_csv(path: Path, rows: List[Tuple[str, str, str, str]]):
    """
    Write CSV sorted by severity:
    connection errors > 5xx > 4xx > others
    """

    def severity(row):
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
            return 3
        return 4

    rows_sorted = sorted(rows, key=severity)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_page", "link_url", "status", "link_type"])
        writer.writerows(rows_sorted)


def write_markdown_report(
    path: Path,
    base_url: str,
    base_status: str,
    pages_scanned: int,
    total_links: int,
    broken_rows: List[Tuple[str, str, str, str]],
):
    md_path = path.with_suffix(".md")

    lines = [
        "# Broken Link Report",
        "",
        f"**Base URL:** {base_url}",
        f"**Base Status:** {base_status}",
        f"**Generated:** {datetime.utcnow().isoformat()}Z",
        "",
        "## Scan Summary",
        f"- Pages scanned: {pages_scanned}",
        f"- Links checked: {total_links}",
        f"- Broken links found: {len(broken_rows)}",
        "",
        "## Broken Links",
        "",
        "| Source Page | URL | Status | Type |",
        "|------------|-----|--------|------|",
    ]

    for source, url, status, link_type in broken_rows:
        lines.append(f"| {source} | {url} | {status} | {link_type} |")

    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_json_summary(
    path: Path,
    base_url: str,
    base_status: str,
    pages_scanned: int,
    total_links: int,
    broken_rows: List[Tuple[str, str, str, str]],
):
    summary = {
        "base_url": base_url,
        "base_status": base_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
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
            "csv": str(path.resolve()),
            "json": str(path.with_suffix(".json").resolve()),
            "markdown": str(path.with_suffix(".md").resolve()),
        },
    }

    with path.with_suffix(".json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


# ---------- Main ----------

def main():
    args = parse_args()
    interrupted = False
    broken_rows: List[Tuple[str, str, str, str]] = []

    def handle_sigint(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\nInterrupted — writing partial report...")

    signal.signal(signal.SIGINT, handle_sigint)

    # --- Base page check ---
    status, error = check_link(args.base_url, timeout=args.timeout, retries=1)
    if error:
        base_status = error
    elif status is not None and status >= 400:
        base_status = str(status)
    else:
        base_status = "ok"

    print(f"Base page status: {base_status}")

    # --- Crawl ---
    pages_scanned, discovered_links = crawl_site(
        base_url=args.base_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        timeout=args.timeout,
    )

    # --- Link checking ---
    for source_page, link_url in tqdm(
        discovered_links,
        total=len(discovered_links),
        desc="Checking links",
        unit="link",
    ):
        if interrupted:
            break

        status, error = check_link(link_url, timeout=args.timeout, retries=1)

        if error or (status is not None and status >= 400):
            broken_rows.append(
                (
                    source_page,
                    link_url,
                    error or str(status),
                    classify_link(args.base_url, link_url),
                )
            )

            if args.verbose:
                print(f"BROKEN {link_url} ({error or status})")

    # --- Write outputs ---
    output_path = Path(args.output)
    write_csv(output_path, broken_rows)
    write_json_summary(
        output_path,
        args.base_url,
        base_status,
        pages_scanned,
        len(discovered_links),
        broken_rows,
    )
    write_markdown_report(
        output_path,
        args.base_url,
        base_status,
        pages_scanned,
        len(discovered_links),
        broken_rows,
    )

    print("\nCrawl complete")
    print(f"Broken links: {len(broken_rows)}")
    print(f"Report written to: {output_path.resolve()}")

    if args.fail_on_broken and broken_rows:
        sys.exit(1)


if __name__ == "__main__":
    main()
