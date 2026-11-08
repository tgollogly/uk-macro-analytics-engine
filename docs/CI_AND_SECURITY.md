# CI and security automation

**Not a security guarantee.** These checks reduce common risks; humans review findings and merge dependency PRs.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Push, PR | **Parallel jobs:** Ruff lint, Python tests (3.11/3.12), Python `security_audit.py` + `pip-audit`, Workers ATS `npm audit` + typecheck + tests |
| [`.github/workflows/security-scheduled.yml`](../.github/workflows/security-scheduled.yml) | Mon–Fri 10:00 **UTC**, `workflow_dispatch` | Weekly daytime scan: pip-audit, npm audit, CodeQL (Python + JS) |

### Cron vs UK time

GitHub Actions cron is **UTC only**. Schedule `0 10 * * 1-5` means **10:00 UTC** Monday–Friday:

- **GMT (winter):** 10:00 UK
- **BST (summer):** 11:00 UK (one hour ahead)

To keep a fixed UK civil time, change the cron when clocks change (Mar/Oct) or accept the one-hour seasonal shift.

## Dependabot

[`.github/dependabot.yml`](../.github/dependabot.yml) opens PRs for pip, npm (`workers/ats-api`), and GitHub Actions weekly (Tuesday 10:00 Europe/London). Limits: 5 pip, 3 npm, 5 actions; **major** version bumps ignored by default (manual review). **No auto-merge.**

## Automated vs human

| Automated | Human review |
|-----------|----------------|
| Ruff, pytest, compile | Merge any Dependabot PR after CI + changelog |
| `pip-audit` / `npm audit` failures on known CVEs | Triaging false positives, accepting documented risks |
| `security_audit.py` heuristics | CodeQL alerts in GitHub Security tab |
| CodeQL on schedule | Enable Advanced Security / branch protection (repo settings) |

## API visibility (agent run)

- `security_and_analysis` on the repo API returned **null** for this integration token — **cannot confirm** Dependabot alerts or CodeQL upload permissions from here.
- Vulnerability-alerts endpoint returned **403** — ensure **Dependabot alerts** are enabled in GitHub → Settings → Code security if you want dashboard alerts.

## Residual limits

- `pip-audit --no-deps` checks **pinned** `requirements.txt` names only, not full transitive lock without a compiled lockfile.
- `npm audit` uses npm advisory DB; devDependencies omitted in CI audit step (`--omit=dev`).
- CodeQL on the **scheduled** workflow only (not duplicated on every PR) to limit Actions minutes.
- No Cloudflare Worker deploy or DNS changes from these workflows.
