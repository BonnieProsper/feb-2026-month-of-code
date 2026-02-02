import argparse
import csv
import signal
import sys
from pathlib import Path
from typing import List, Tuple

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
        "--verbose",
        action="store_true",
        help="Print broken links as they are found",
    )

    return parser.parse_args()


# ---------- Output ----------

def write_csv(path: Path, rows: List[Tuple[str, str, str]]):
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
        writer.writerow(["source_page", "link_url", "status"])
        writer.writerows(rows_sorted)


# ---------- Color helpers ----------

def red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


# ---------- Main ----------

def main():
    args = parse_args()
    broken_rows: List[Tuple[str, str, str]] = []
    interrupted = False

    # Graceful Ctrl+C handling
    def handle_sigint(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\nInterrupted — writing partial report...")

    signal.signal(signal.SIGINT, handle_sigint)

    # --- Root page check ---
    status, error = check_link(args.base_url, timeout=args.timeout, retries=1)
    if error or (status is not None and status >= 400):
        broken_rows.append(
            (args.base_url, args.base_url, error or str(status))
        )
        print(red(f"Base page issue: {args.base_url} → {error or status}"))
    else:
        print(green(f"Base page OK: {args.base_url}"))

    # --- Crawl ---
    pages_scanned, discovered_links = crawl_site(
        base_url=args.base_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        timeout=args.timeout,
        progress_callback=lambda current, total, url: print(
            f"[Page {current}/{total}] Crawling: {url}"
        ),
    )

    # --- Link checking ---
    if not discovered_links:
        print("\nNo internal links discovered.")
    else:
        print(f"\nChecking {len(discovered_links)} links...\n")

        for source_page, link_url in tqdm(
            discovered_links,
            desc="Checking links",
            unit="link",
        ):
            if interrupted:
                break

            status, error = check_link(link_url, timeout=args.timeout, retries=1)

            if error:
                broken_rows.append((source_page, link_url, error))
                if args.verbose:
                    print(red(f"ERROR  {link_url} ({error})"))

            elif status is not None and status >= 400:
                broken_rows.append((source_page, link_url, str(status)))
                if args.verbose:
                    print(red(f"{status}  {link_url}"))

            elif args.verbose:
                print(green(f"OK     {link_url}"))

    # --- Write report ---
    output_path = Path(args.output)
    write_csv(output_path, broken_rows)

    # --- Summary ---
    print("\nCrawl complete")
    print(f"Pages scanned: {pages_scanned}")
    print(f"Links checked: {len(discovered_links)}")
    print(f"Broken links found: {len(broken_rows)}")
    print(f"Report written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
