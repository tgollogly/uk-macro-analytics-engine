# CI and security automation

**Not a security guarantee.** These checks reduce common risks; humans review findings and merge dependency PRs.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Push, PR | **Parallel jobs:** Ruff; Python tests (3.11/3.12); `security_audit.py` + full `pip-audit` on installed deps; Workers typecheck/tests + npm audit (runtime **and** dev) |
| [`.github/workflows/security-scheduled.yml`](../.github/workflows/security-scheduled.yml) | **Tuesday 10:00 UTC** (once weekly), `workflow_dispatch` | Same pip/npm audits + **CodeQL** (not rerun on every PR) |

### Weekly schedule (low compute)

| Item | Schedule |
|------|----------|
| **Security (scheduled)** | `0 10 * * 2` → **one run per week**, Tuesday 10:00 **UTC** |
| **UK time** | 10:00 **GMT** (Nov–Mar) or 11:00 **BST** (Mar–Oct) — cron does not follow DST |
| **Dependabot** | Tuesday 10:00 **Europe/London** (opens update PRs; not the same as pip-audit job minutes) |
| **CI pip-audit / npm audit** | On each push/PR only (catches regressions before merge) |

## Audit scope

| Tool | What is scanned |
|------|-----------------|
| **pip-audit** | After `pip install -r requirements-dev.txt`, audits **installed environment** (direct + **transitive** PyPI packages). No `--no-deps` / `--disable-pip`. |
| **npm audit (production)** | `npm ci` then `npm audit --omit=dev --audit-level=high` |
| **npm audit (dev)** | `npm audit --only=dev --audit-level=high` on the same lockfile (devDependencies reported separately, not hidden) |
| **security_audit.py** | Repo heuristics (secrets patterns, etc.) |
| **CodeQL** | Python + JavaScript; `security-and-quality` query pack on **scheduled** workflow only |

## Dependabot

[`.github/dependabot.yml`](../.github/dependabot.yml) opens PRs for pip, npm (`workers/ats-api`), and GitHub Actions weekly. Limits: 5 pip, 3 npm, 5 actions; **major** bumps ignored by default. **No auto-merge.**

## CodeQL — not proven until scheduled run succeeds

- The **scheduled** workflow needs `security-events: write` on the CodeQL job (configured).
- **First successful CodeQL upload** typically requires the workflow on the default branch and, for private repos, GitHub Advanced Security. **Public** repos usually upload to the Security tab once the workflow runs.
- This agent **cannot confirm** Advanced Security / alert settings (`security_and_analysis` null, vulnerability-alerts API 403 on the cloud token).
- **`workflow_dispatch`** on a feature branch may not run until the workflow file exists on `main` — treat CodeQL as **unproven until parent merges and triggers** (or runs from `main`).

## Automated vs human

| Automated | Human review |
|-----------|----------------|
| Ruff, pytest, compile | Merge Dependabot PRs after CI |
| pip-audit / npm audit failures | Accept or fix CVEs; constrain bumps in `requirements*.txt` / lockfile |
| `security_audit.py` | CodeQL alerts in GitHub Security tab |
| Weekly scheduled scan | Adjust cron for fixed UK hour if needed |

## Residual limits

- pip-audit reflects **PyPI OSV** data; unpinned ecosystem packages on self-hosted runners are out of scope (GHA uses clean `setup-python` + project install).
- npm audit advisories differ from Snyk/CodeQL findings.
- No Cloudflare Worker deploy or DNS changes from these workflows.
