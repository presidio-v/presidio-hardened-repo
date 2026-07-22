---
status: working sheet
date: 2026-07-20
owner: Vladimir Stantchev
target: OpenSSF Best Practices Badge — passing level (score 5 on Scorecard CII-Best-Practices)
project_url: https://github.com/presidio-v/presidio-hardened-x402
related:
  - plan/atheris-fuzz-harness-prompt.md
---

# CII Best Practices — passing-level answer sheet

Fill-in sheet for <https://www.bestpractices.dev>. 67 passing criteria.

## Before you start

1. **Register the URL as exactly** `https://github.com/presidio-v/presidio-hardened-x402`.
   Scorecard does a literal DB string match. A trailing slash, `www.`, or the PyPI URL
   returns `NotFound` → score 0 despite a real badge.
2. **Log in with GitHub but decline the org grant.** BadgeApp requests `read:org` and no code
   path consumes it. Entry ownership is internal to its database.
3. ~~Merge `docs/community-health` first.~~ **Done 2026-07-21** (PR #87, squash `ab4a5ec`).
   `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` are on `main` and their URLs resolve. The
   fuzzing work (PR #88, `31786b0`) and the collision fix it surfaced (PR #89, `a8d0994`)
   are also merged, so every answer below is now backed by live `main` — nothing is
   pending.

Shorthand below: `REPO` = `https://github.com/presidio-v/presidio-hardened-x402`.

---

## Basics — project website content

| Criterion | Answer | Justification / URL |
|---|---|---|
| `description_good` | **Met** | `REPO#readme` — README opens with what the library does and the problem it solves (pre-transmission enforcement on x402 payment requests). |
| `interact` | **Met** | `REPO#contributing-and-support` — README section covers obtaining (PyPI), feedback (issues), security reports (SECURITY.md), and contributing. |
| `contribution` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md` — "How changes are made" documents the fork → branch → PR flow against `main`. |
| `contribution_requirements` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md#requirements-for-acceptable-contributions` — ruff style config, test policy, security-change rules, dependency bar. |

## Basics — FLOSS license

| Criterion | Answer | Justification / URL |
|---|---|---|
| `floss_license` | **Met** | MIT. |
| `floss_license_osi` | **Met** | MIT is OSI-approved. |
| `license_location` | **Met** | URL: `REPO/blob/main/LICENSE` |

## Basics — documentation

| Criterion | Answer | Justification / URL |
|---|---|---|
| `documentation_basics` | **Met** | README + `docs/quickstarts/` (Coinbase CDP, LangChain, CrewAI). |
| `documentation_interface` | **Met** | README API section, `SEMVER.md` defines the public API surface (`presidio_x402.__all__`), `docs/` covers the evidence and MiCA interfaces. |

## Basics — other

| Criterion | Answer | Justification / URL |
|---|---|---|
| `sites_https` | **Met** | GitHub, PyPI, and `screen.presidio-group.eu` are all HTTPS. |
| `discussion` | **Met** | GitHub Issues: `REPO/issues` — searchable, URL-addressable, open, no proprietary client. |
| `english` | **Met** | All docs and issue handling in English. |
| `maintained` | **Met** | Active; v0.9.1 released 2026-07. |

## Change control — repository

| Criterion | Answer | Justification / URL |
|---|---|---|
| `repo_public` | **Met** | `REPO` |
| `repo_track` | **Met** | git. |
| `repo_interim` | **Met** | Feature and fix branches are pushed between releases; PR-based flow. |
| `repo_distributed` | **Met** | git. |

## Change control — versioning

| Criterion | Answer | Justification / URL |
|---|---|---|
| `version_unique` | **Met** | Semver per release, tagged. |
| `version_semver` | **Met** | `REPO/blob/main/SEMVER.md` — documents the pre-1.0 semver profile. |
| `version_tags` | **Met** | Every release is a git tag, SSH-signed and GitHub-verified. |

## Change control — release notes

| Criterion | Answer | Justification / URL |
|---|---|---|
| `release_notes` | **Met** | URL: `REPO/blob/main/CHANGELOG.md` — Keep a Changelog format, hand-written, not VCS log output. |
| `release_notes_vulns` | **Met** | CHANGELOG names each CVE/GHSA fixed by dependency floor bumps (e.g. CVE-2026-44431/44432 urllib3, CVE-2026-45134 langsmith, CVE-2026-44843 langchain-core, GHSA-mf9w-mj56-hr94 python-dotenv). |

## Reporting — bug reports

| Criterion | Answer | Justification / URL |
|---|---|---|
| `report_process` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md#reporting-bugs-and-requesting-features` |
| `report_tracker` | **Met** | GitHub Issues. |
| `report_responses` | **Met** | All external reports in the window received a maintainer response: #6 (opened 2026-04-14, closed 2026-04-16), #17 (8 comments, closed 2026-06-20), #18 (closed 2026-05-03), #81 (opened 2026-07-05, responded). |
| `enhancement_responses` | **Met** | #6, #17, #18 were enhancement/fixture proposals; all answered, three of four closed. |
| `report_archive` | **Met** | URL: `REPO/issues?q=is%3Aissue` — public and searchable. |

## Reporting — vulnerability reports

| Criterion | Answer | Justification / URL |
|---|---|---|
| `vulnerability_report_process` | **Met** | URL: `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` |
| `vulnerability_report_private` | **Met** | URL: `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — private GitHub Security Advisory via the Security tab; 5-business-day ack, 30-day patch target. |
| `vulnerability_report_response` | **N/A** | No externally reported vulnerabilities in the last 6 months — the repo has zero security advisories filed. Internally found issues were fixed directly (v0.9.1). |

## Quality — build system

| Criterion | Answer | Justification / URL |
|---|---|---|
| `build` | **Met** | PEP 517 via hatchling; `pip install -e ".[dev]"` rebuilds from source. |
| `build_common_tools` | **Met** | hatchling / pip / uv. |
| `build_floss_tools` | **Met** | Entire toolchain is FLOSS. |

## Quality — automated test suite

| Criterion | Answer | Justification / URL |
|---|---|---|
| `test` | **Met** | 39 test modules under `tests/`, MIT-licensed with the project. How to run: `CONTRIBUTING.md#local-verification` and `.github/workflows/ci.yml`. |
| `test_invocation` | **Met** | `pytest tests/` — the standard Python convention. |
| `test_most` | **Met** | Coverage gate enforced at 90% (`--cov-fail-under=90`), plus a 7-check end-to-end conformance suite. |
| `test_continuous_integration` | **Met** | GitHub Actions on every push and PR, Python 3.10–3.13 matrix. |

## Quality — new functionality testing

| Criterion | Answer | Justification / URL |
|---|---|---|
| `test_policy` | **Met** | `CONTRIBUTING.md#tests` — written policy that functional changes ship with tests and fixes ship with regression tests. |
| `tests_are_added` | **Met** | Worked example: PR #89 (the replay-fingerprint collision fix) shipped with its regression test in the same PR — the two colliding 31-digit amounts, plus a parametrised guard pinning the pre-existing trailing-zero equivalences. Also the v0.8.1 PHONE span fix landed with its regression test. |
| `tests_documented_added` | **Met** | The policy is in the contribution instructions themselves (`CONTRIBUTING.md`). |

## Quality — warning flags

| Criterion | Answer | Justification / URL |
|---|---|---|
| `warnings` | **Met** | ruff, enforced in CI (`ruff check` + `ruff format --check`). |
| `warnings_fixed` | **Met** | CI fails on any finding; `main` is clean. |
| `warnings_strict` | **Met** | Rule sets `E, F, W, I, N, UP, S, B, A, C4, SIM, TCH` — well beyond defaults, includes bandit security rules (`S`). Only `S101`, `S603`, `S607` are excluded, with rationale. |

## Security — secure development knowledge

| Criterion | Answer | Justification / URL |
|---|---|---|
| `know_secure_design` | **Met** | Maintainer designs hardened middleware across the presidio-hardened-* family; the project applies least privilege, fail-closed defaults, defence in depth, and documented trust boundaries. Independent multi-round third-party security audit cleared for v0.8.0. |
| `know_common_errors` | **Met** | Documented threat model and 8 adversary attack chains with mitigations; SSRF, replay, injection, and PII-exposure classes each have named countermeasures and regression tests. |

## Security — cryptographic practices

| Criterion | Answer | Justification / URL |
|---|---|---|
| `crypto_published` | **Met** | SHA-256, HMAC-SHA256, Ed25519 only. |
| `crypto_call` | **Met** | Calls `hashlib`, `hmac`, `secrets`, and `cryptography`. No primitive is re-implemented. |
| `crypto_floss` | **Met** | All of the above are FLOSS. |
| `crypto_keylength` | **Met** | 256-bit HMAC keys, SHA-256 digests, Ed25519 — all above NIST 2030 minimums. |
| `crypto_working` | **Met** | No MD4, MD5, single DES, RC4, or Dual_EC_DRBG anywhere. |
| `crypto_weaknesses` | **Met** | No SHA-1 and no CBC-mode dependency in default paths. |
| `crypto_pfs` | **N/A** | Implements no key-agreement protocol of its own; transport PFS is provided by TLS in the HTTP layer. |
| `crypto_password_storage` | **N/A** | Stores no external-user passwords. |
| `crypto_random` | **Met** | `secrets.token_bytes(32)` for audit-chain keys (`audit_log.py`). |

## Security — delivery

| Criterion | Answer | Justification / URL |
|---|---|---|
| `delivery_mitm` | **Met** | Distributed over HTTPS via PyPI and GitHub; published through PyPI Trusted Publishing (GitHub OIDC, no long-lived token). |
| `delivery_unsigned` | **Met** | No hash is fetched over plain HTTP. Release tags are SSH-signed and GitHub-verified. |

## Security — known vulnerabilities

| Criterion | Answer | Justification / URL |
|---|---|---|
| `vulnerabilities_fixed_60_days` | **Met** | No known unpatched medium+ vulnerabilities. Dependabot plus `pip-audit` in CI; v0.9.1 shipped as a security patch. |
| `vulnerabilities_critical_fixed` | **Met** | Recent criticals in dependencies were closed by floor bumps within days (see CHANGELOG). |

## Security — other

| Criterion | Answer | Justification / URL |
|---|---|---|
| `no_leaked_credentials` | **Met** | Verified: no `.env`, `.pem`, key, or credential-shaped file appears anywhere in this repository's history. Patent and evidence material lives in a separate private repository and was never present here. |

## Analysis — static

| Criterion | Answer | Justification / URL |
|---|---|---|
| `static_analysis` | **Met** | CodeQL (results uploaded to GitHub code scanning) plus bandit as a Python-specific second pass — `.github/workflows/codeql.yml`. |
| `static_analysis_common_vulnerabilities` | **Met** | CodeQL's security query suite and bandit both target common vulnerability classes; ruff's `S` rule set adds a third layer in-line. |
| `static_analysis_fixed` | **Met** | Findings are triaged and fixed before release; the v0.8.0 audit cycle cleared independently. |
| `static_analysis_often` | **Met** | CodeQL and bandit run on every push and PR to `main`, plus a weekly scheduled run. |

## Analysis — dynamic

| Criterion | Answer | Justification / URL |
|---|---|---|
| `dynamic_analysis` | **Met** | Atheris coverage-guided fuzz harnesses over the canonicalisation and digest functions (`fuzz/`), run in CI on every push and PR (`.github/workflows/ci.yml`, `Fuzz (Atheris)` job). Merged in PR #88; the `Fuzz (Atheris)` job is green on `main`. On its first run it found a real replay-fingerprint collision, fixed in PR #89 — i.e. the dynamic analysis is not decorative, it has already caught a defect. |
| `dynamic_analysis_unsafe` | **N/A** | Pure Python; no memory-unsafe language in the codebase. |
| `dynamic_analysis_enable_assertions` | **Met** | The suite is assertion-based pytest; ruff's `S101` exclusion exists specifically so assertions stay enabled in tests. |
| `dynamic_analysis_fixed` | **Met** | No unfixed medium+ findings. |

---

## Sequencing

1. ~~Merge `docs/community-health`~~ — **done** (PR #87, `ab4a5ec`). URLs resolve.
2. ~~Merge the Atheris branch~~ — **done** (PR #88, `31786b0`). `dynamic_analysis` is
   honestly Met; the collision it surfaced is fixed (PR #89, `a8d0994`). Scorecard Fuzzing
   goes 0 → 10 on its next run, independently of the badge.
3. **← YOU ARE HERE.** Register at bestpractices.dev and fill in from this sheet. All 43
   MUSTs are satisfiable without overclaiming, and every cited URL is live on `main`.
4. Scorecard picks up the badge on its next weekly run — CII goes 0 → 5.

Scorecard last ran 2026-07-20 (overall 7.5). With Fuzzing 0 → 10 and CII 0 → 5 both landing,
expect roughly +1 overall on the next weekly run — the exact figure depends on Scorecard's
current weightings, so treat ~8.2–8.5 as an estimate, not a promise.

## Deliberately not claimed

Silver (score 7) is **not** honestly reachable while the project is single-maintainer.
`access_continuity` is a silver MUST requiring the project to survive the loss of any one
person within a week; the release signing key exists only in the maintainer's Bitwarden vault.
`bus_factor` (SHOULD ≥ 2), `governance`, and `roles_responsibilities` have the same root cause.

A second maintainer with org access and release capability would resolve all four, and would
simultaneously move Scorecard's Code-Review check off 0 — Scorecard credits the *merger* of
another person's PR as an approver. That single change is the highest-leverage item across
all three low checks.
