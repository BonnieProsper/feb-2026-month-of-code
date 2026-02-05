import argparse
import sys

from spf import analyze_spf
from dmarc import analyze_dmarc
from dkim import check_dkim
from report import normalize_findings, format_console_report, format_json_report


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
    parser.add_argument(
        "--dkim-selector",
        action="append",
        help="Optional DKIM selector(s) to check. Can be used multiple times.",
    )

    args = parser.parse_args()

    # Collect raw findings from all modules
    raw_findings = []
    raw_findings.extend(analyze_spf(args.domain))
    raw_findings.extend(analyze_dmarc(args.domain))
    raw_findings.extend(check_dkim(domain=args.domain, selectors=args.dkim_selector))

    # Normalize findings for consistent reporting
    findings = normalize_findings(raw_findings)

    # Output
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
