# Email Deliverability Analyzer

A production-style CLI tool for analyzing **email authentication and brand trust
signals** for a domain.

It evaluates SPF, DKIM, DMARC, and BIMI configurations with a focus on
**operator-relevant risk**, **provider-aware interpretation**, and
**CI-compatible reporting**.

This is not a remediation tool.
It does not modify DNS or attempt to “fix” configurations.
It surfaces what matters.

---

## What this tool analyzes

### Authentication
- SPF authorization scope and risk
- DKIM selector presence and record integrity
- DMARC enforcement posture and alignment signals

### Brand Indicators
- BIMI record presence and correctness
- SVG logo safety validation
- VMC authority certificate sanity checks

### Context
- Mailbox provider inference (Google / Microsoft)
- Provider-aware findings (informational, not speculative)

---

## Output formats

- **Console** — human-readable, grouped by severity
- **JSON** — machine-readable, stable schema
- **SARIF** — compatible with GitHub Code Scanning

The CLI supports a strict mode that can fail CI on WARN findings.

---

## Why this exists

Email deliverability failures are rarely caused by missing records alone.
They are caused by:

- misalignment between mechanisms
- weak or permissive policies
- unsafe brand assets
- provider-specific enforcement differences

This project focuses on **observable failure modes**, not RFC reenactment.

---

## Usage

```bash
python cli.py example.com
python cli.py example.com --format json
python cli.py example.com --strict
```

Optional DKIM selectors:
```bash
python cli.py example.com --dkim-selector s1 --dkim-selector google
```

## Threat model
### In scope

- Domain spoofing via weak authentication
- Brand impersonation via unsafe BIMI assets
- Silent deliverability degradation
- Provider-specific enforcement gaps

### Out of scope

- Message-level DKIM verification
- SMTP interception or abuse detection
- Reputation scoring
- Automatic remediation

### Security considerations

- All network fetches use strict timeouts
- SVG parsing enforces size and element restrictions
- XML entity expansion is avoided
- Certificates are parsed, not trusted blindly
- No dynamic code execution or shell access

### Design principles

- Detection over speculation
- High-signal findings only
- Explicit severity mapping
- Provider-aware interpretation
- Safe by default