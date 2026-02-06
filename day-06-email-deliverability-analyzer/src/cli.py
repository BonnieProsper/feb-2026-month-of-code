import argparse
import json
import sys

from spf import analyze_spf
from dmarc import analyze_dmarc
from dkim import check_dkim
from bimi import analyze_bimi
from report import (
    normalize_findings,
    format_console_report,
    format_json_report,
    format_sarif_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze email deliverability configuration for a domain."
    )
    parser.add_argument("domain")
    parser.add_argument(
        "--dkim-selector",
        action="append",
        help="DKIM selector(s) to check",
    )
    parser.add_argument(
        "--format",
        choices=("console", "json", "sarif"),
        default="console",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN findings as failures",
    )

    args = parser.parse_args()

    raw_findings = []
    raw_findings.extend(analyze_spf(args.domain))
    raw_findings.extend(analyze_dmarc(args.domain))
    raw_findings.extend(check_dkim(args.domain, args.dkim_selector))
    raw_findings.extend(analyze_bimi(args.domain))

    findings = normalize_findings(raw_findings)

    if args.format == "json":
        print(format_json_report(findings))
    elif args.format == "sarif":
        print(json.dumps(format_sarif_report(findings), indent=2))
    else:
        print(format_console_report(findings))

    has_fail = any(f["severity"] == "FAIL" for f in findings)
    has_warn = any(f["severity"] == "WARN" for f in findings)

    if args.strict:
        return 1 if (has_fail or has_warn) else 0

    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
