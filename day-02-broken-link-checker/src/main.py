import argparse
import csv
from pathlib import Path
import sys
import signal

from src.crawler import crawl_site
from src.checker import check_link


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple broken link checker for a single domain"
    )

    parser.add_argument("base_url", help="Base URL to crawl")

    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Maximum crawl depth (default: 2)",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to crawl (default: 100)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for HTTP requests (default: 5)",
    )

    parser.add_argument(
        "--output",
        default="broken_links.csv",
        help="CSV output file (default: broken_links.csv)",
    )

    return parser.parse_args()


def write_csv(path: Path, rows: list[tuple[str, str, str]]):
    # Sort by severity: connection errors > 5xx > 4xx
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
        writer.writerow(["source_page", "link_url", "status"])
        writer.writerows(rows_sorted)


def main():
    args = parse_args()
    broken_rows: list[tuple[str, str, str]] = []
    interrupted = False

    def handle_sigint(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\nCrawl interrupted by user. Writing partial report...")
        # Will exit crawl loop gracefully

    signal.signal(signal.SIGINT, handle_sigint)

    # Crawl site
    pages_scanned, discovered_links = crawl_site(
        base_url=args.base_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        timeout=args.timeout,
        progress_callback=lambda current, total, url: print(f"[Page {current}/{total}] Crawling: {url}")
    )

    # Check links with progress
    total_links = len(discovered_links)
    for i, (source_page, link_url) in enumerate(discovered_links, start=1):
        if interrupted:
            break

        status, error = check_link(link_url, timeout=args.timeout, retries=1)
        if error:
            broken_rows.append((source_page, link_url, error))
        elif status is not None and status >= 400:
            broken_rows.append((source_page, link_url, str(status)))

        # Print progress every 5 links
        if i % 5 == 0 or i == total_links:
            print(f"[Link {i}/{total_links}] Checked: {link_url}")

    # Write CSV
    output_path = Path(args.output)
    write_csv(output_path, broken_rows)

    print("\nCrawl complete")
    print(f"Pages scanned: {pages_scanned}")
    print(f"Links checked: {len(discovered_links)}")
    print(f"Broken links found: {len(broken_rows)}")
    print(f"Report written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
