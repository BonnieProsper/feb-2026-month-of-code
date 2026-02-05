import argparse
import sys

from .spf import analyze_spf
from .report import normalize_findings, format_console_report, format_json_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze email deliverability configuration for a domain."
    )
    parser.add_argument(
        "domain",
        help="Domain to analyze (e.g. example.com)",
    )
    parser.add_argument(
        "--format",
        choices=("console", "json"),
        default="console",
        help="Output format (default: console)",
    )

    args = parser.parse_args()

    raw_findings = []

    # SPF
    raw_findings.extend(analyze_spf(args.domain))

    findings = normalize_findings(raw_findings)

    if args.format == "json":
        output = format_json_report(findings)
    else:
        output = format_console_report(findings)

    print(output)

    # Exit non-zero if any FAIL findings exist
    has_failures = any(f["severity"] == "FAIL" for f in findings)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
