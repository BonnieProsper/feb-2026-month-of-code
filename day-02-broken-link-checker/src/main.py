import argparse
import csv
from pathlib import Path

from crawler import crawl_site
from checker import check_link


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
        "--output",
        default="broken_links.csv",
        help="CSV output file (default: broken_links.csv)",
    )

    return parser.parse_args()


def write_csv(path: Path, rows: list[tuple[str, str, str]]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_page", "link_url", "status"])
        writer.writerows(rows)


def main():
    args = parse_args()

    pages_scanned, discovered_links = crawl_site(
        base_url=args.base_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
    )

    broken_rows: list[tuple[str, str, str]] = []

    for source_page, link_url in discovered_links:
        status, error = check_link(link_url)

        if error:
            broken_rows.append((source_page, link_url, error))
        elif status is not None and status >= 400:
            broken_rows.append((source_page, link_url, str(status)))

    output_path = Path(args.output)
    write_csv(output_path, broken_rows)

    print("Crawl complete")
    print(f"Pages scanned: {pages_scanned}")
    print(f"Links checked: {len(discovered_links)}")
    print(f"Broken links found: {len(broken_rows)}")
    print(f"Report written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
