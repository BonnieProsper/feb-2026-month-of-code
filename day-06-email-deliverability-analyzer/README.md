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

## Interpreting results for large providers

Some large mailbox providers (e.g. Google, Yahoo, Microsoft) do not publish
SPF, DKIM, or DMARC records at their organizational apex domains.

This is intentional.

These providers authenticate mail using:
- delegated subdomains
- per-product sending domains
- organizational DMARC inheritance

When analyzing such domains, this tool may report missing or non-enforcing
authentication records. These findings are **informational**, not an assertion
of misconfiguration.

The analyzer evaluates:
- what is observable at the queried domain
- what a receiving MTA would see at lookup time

It does not attempt to infer internal provider infrastructure or
non-public policy delegation.

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
### Running the CLI

This project is structured as a Python package.
Run the CLI using module execution from the repository root:

```bash
python -m src.cli example.com

## Usage

```bash
python -m src.cli example.com
python -m src.cli example.com --format json
python -m src.cli example.com --strict
python -m src.cli example.com --dkim-selector s1
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