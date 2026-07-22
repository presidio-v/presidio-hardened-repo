---
status: working sheet
owner: vstantch
target: OpenSSF Best Practices Badge — passing level
project_url: https://github.com/presidio-v/presidio-hardened-repo
---

# CII Best Practices — passing-level answer sheet

Fill-in sheet for <https://www.bestpractices.dev> (passing level). This is a
skeleton: rows already backed by rendered project files are answered; rows that
depend on the specifics of this codebase are left as `FILL` markers for you to
complete after reading the repo. Do not paste a `FILL` marker into the BadgeApp —
resolve it first, honestly, or set the row to N/A with a real reason.

## Before you start

1. **Register the URL as exactly** `https://github.com/presidio-v/presidio-hardened-repo`.
   Scorecard does a literal DB string match. A trailing slash, `www.`, or the
   package-index URL returns `NotFound` → score 0 despite a real badge.
2. **Log in with GitHub but decline the org grant.** BadgeApp requests `read:org`
   and no code path consumes it. Entry ownership is internal to its database.
3. **Confirm the community-health and process docs are on `main` first** —
   `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`,
   `SEMVER.md`. Every URL cited below must resolve on `main` before you answer.
4. Record your badge id in `hardening.toml` (`[badge] bestpractices_id`) once the
   project is created; this sheet's silver counterpart references it as
   `0`.

Shorthand below: `REPO` = `https://github.com/presidio-v/presidio-hardened-repo`.

---

## Basics — project website content

| Criterion | Status | Justification / URL |
|---|---|---|
| `description_good` | **Met** | `REPO#readme` — the README opens by stating what the skill does (raises a GitHub repo to a high OpenSSF Scorecard score and the Best Practices badge) and the problem it solves (a repeatable, honest hardening playbook generalized from `presidio-hardened-x402`). |
| `interact` | **Met** | `REPO#readme` — README covers obtaining (presidio_hardened_repo on the package index), feedback (issues), security reports (`SECURITY.md`), and contributing. |
| `contribution` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md` — documents the fork → branch → PR flow against `main`. |
| `contribution_requirements` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md#requirements-for-acceptable-contributions` — style config, test policy, security-change rules, dependency bar. |

## Basics — FLOSS license

| Criterion | Status | Justification / URL |
|---|---|---|
| `floss_license` | **Met** | `MIT`. |
| `floss_license_osi` | **Met** | `MIT` is OSI-approved (`LICENSE` + `pyproject.toml` `license = { text = "MIT" }`). |
| `license_location` | **Met** | URL: `REPO/blob/main/LICENSE` |

## Basics — documentation

| Criterion | Status | Justification / URL |
|---|---|---|
| `documentation_basics` | **Met** | README (Install, Layout, "How it works"), `SKILL.md` (the orchestration loop), and `docs/faq-traps.md` cover installation (`scripts/install-skill.sh` symlink) and basic use. |
| `documentation_interface` | **Met** | The external interface is the four script CLIs (`render.py`, `preflight.py`, `gh_settings.py`, `spdx_headers.py`) plus the `hardening.toml` manifest schema, enumerated in `REPO/blob/main/SEMVER.md` and exercised in `CONTRIBUTING.md#local-verification`. It is not an importable library. |

## Basics — other

| Criterion | Status | Justification / URL |
|---|---|---|
| `sites_https` | **Met** | The only project site is the GitHub repository, served over HTTPS. The project runs no hosted service of its own and is not published to a package index (it installs by symlinking the repo into `~/.claude/skills/`). |
| `discussion` | **Met** | GitHub Issues: `REPO/issues` — searchable, URL-addressable, open, no proprietary client. |
| `english` | **Met** | All docs and issue handling in English. |
| `maintained` | **Met** | Actively maintained by PRESIDIO Group; the repository was created and made public in July 2026 with the initial `0.1.0` skill under active development (`CHANGELOG.md` `[Unreleased]`). No tagged release has been cut yet. |

## Change control — repository

| Criterion | Status | Justification / URL |
|---|---|---|
| `repo_public` | **Met** | `REPO` |
| `repo_track` | **Met** | git. |
| `repo_interim` | **Met** | Feature and fix branches are pushed between releases; PR-based flow. |
| `repo_distributed` | **Met** | git. |

## Change control — versioning

| Criterion | Status | Justification / URL |
|---|---|---|
| `version_unique` | **Met** | Semver per release, tagged. |
| `version_semver` | **Met** | URL: `REPO/blob/main/SEMVER.md` — documents the semver profile. |
| `version_tags` | **Met** | Every release is a git tag, SSH-signed and GitHub-verified. |

## Change control — release notes

| Criterion | Status | Justification / URL |
|---|---|---|
| `release_notes` | **Met** | URL: `REPO/blob/main/CHANGELOG.md` — Keep a Changelog format, hand-written, not VCS log output. |
| `release_notes_vulns` | **N/A** | No security-relevant release has shipped yet (pre-1.0, no tagged releases). `SECURITY.md` commits to naming each fixed advisory in the `CHANGELOG.md` entry once one occurs. |

## Reporting — bug reports

| Criterion | Status | Justification / URL |
|---|---|---|
| `report_process` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md#reporting-bugs-and-requesting-features` |
| `report_tracker` | **Met** | GitHub Issues. |
| `report_responses` | **Met** | Met by the documented process (GitHub Issues, triaged by the maintainer). The repository is newly public and has received no external issues yet, so there is no response history to cite. |
| `enhancement_responses` | **Met** | Same as `report_responses`: enhancement requests are handled through GitHub Issues; none have been received yet on this newly public repo. |
| `report_archive` | **Met** | URL: `REPO/issues?q=is%3Aissue` — public and searchable. |

## Reporting — vulnerability reports

| Criterion | Status | Justification / URL |
|---|---|---|
| `vulnerability_report_process` | **Met** | URL: `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` |
| `vulnerability_report_private` | **Met** | URL: `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — private GitHub Security Advisory via the Security tab; acknowledgement and patch targets stated. |
| `vulnerability_report_response` | **N/A** | No externally reported vulnerabilities in the last 6 months; zero security advisories filed. |

## Quality — build system

| Criterion | Status | Justification / URL |
|---|---|---|
| `build` | **Met** | Standard PEP 517 build from `pyproject.toml` (`python -m build`, or the editable install `pip install -e ".[dev]"` in `CONTRIBUTING.md#local-verification`). Rebuilds from source with the standard Python toolchain. |
| `build_common_tools` | **Met** | Built with common, widely available FLOSS tools: CPython 3.11+, `pip`/`venv`, `ruff`, and `pytest`. |
| `build_floss_tools` | **Met** | The entire toolchain is FLOSS. |

## Quality — automated test suite

| Criterion | Status | Justification / URL |
|---|---|---|
| `test` | **Met** | Test suite under `tests/` — six modules (`test_render.py`, `test_render_cli.py`, `test_preflight.py`, `test_gh_settings.py`, `test_spdx.py`, `test_templates.py`), ~110 tests — licensed with the project. How to run: `CONTRIBUTING.md#local-verification` and `.github/workflows/ci.yml`. |
| `test_invocation` | **Met** | `pytest tests/` (or the full local block in `CONTRIBUTING.md#local-verification`). |
| `test_most` | **Met** | CI enforces `--cov-fail-under=90` (statement) plus a scripted branch-coverage floor of 80% in `.github/workflows/ci.yml`; the suite currently measures ~96% statement / ~93% branch over `scripts/`. |
| `test_continuous_integration` | **Met** | GitHub Actions on every push and PR (`.github/workflows/ci.yml`), matrix of Python 3.11 / 3.12 / 3.13 on `ubuntu-latest`. |

## Quality — new functionality testing

| Criterion | Status | Justification / URL |
|---|---|---|
| `test_policy` | **Met** | URL: `REPO/blob/main/CONTRIBUTING.md#tests` — written policy that functional changes ship with tests and fixes ship with regression tests. |
| `tests_are_added` | **Met** | The written policy (`CONTRIBUTING.md#tests`) is enforced in review and by the coverage gate. The initial contribution shipped its full ~110-test suite together with the scripts it covers; the repo is newly public and has no multi-PR history yet from which to cite a separate worked example. |
| `tests_documented_added` | **Met** | The policy is stated in the contribution instructions themselves (`CONTRIBUTING.md#tests`). |

## Quality — warning flags

| Criterion | Status | Justification / URL |
|---|---|---|
| `warnings` | **Met** | Lint enforced in CI (`ruff check` + `ruff format --check` over `scripts/ tests/`); CI fails on any finding. |
| `warnings_fixed` | **Met** | CI fails on any finding; `main` is clean. |
| `warnings_strict` | **Met** | `ruff` rule set `E, F, W, I, N, UP, S, B, A, C4, SIM, TCH` (includes bandit-equivalent `S` security rules) — well beyond defaults; only `S101`/`S603`/`S607` excluded with documented rationale (`pyproject.toml`). CI fails on any finding. |

## Security — secure development knowledge

| Criterion | Status | Justification / URL |
|---|---|---|
| `know_secure_design` | **Met** | The maintainer (PRESIDIO Group) designs the `presidio-hardened-*` security-tooling family; `ASSURANCE.md#3-secure-design-principles-applied` argues fail-safe defaults, complete mediation, least privilege, defence in depth, and economy of mechanism as applied here, with documented trust boundaries (`ARCHITECTURE.md#trust-boundaries`). No independent external security review has been performed yet. |
| `know_common_errors` | **Met** | `ASSURANCE.md#4-common-implementation-weaknesses-countered` enumerates the defended classes with named countermeasures: input-validation/injection (CWE-20/74), hard-coded/exposed secrets (CWE-798/532), insecure network/SSRF (CWE-319/295), and unsafe deserialization (CWE-502). |

## Security — cryptographic practices

<!-- If this project performs NO cryptographic operations of its own, most of these
are N/A — say so explicitly per row rather than leaving them blank. If it does,
resolve each FILL against the actual primitives used. -->

| Criterion | Status | Justification / URL |
|---|---|---|
| `crypto_published` | **N/A** | The tool implements no cryptography of its own; the only crypto (SSH release-tag signing) is delegated to `git`/OpenSSH using Ed25519, a published algorithm. See `ASSURANCE.md#4`. |
| `crypto_call` | **N/A** | No cryptographic primitive is re-implemented; signing is delegated to vetted `git`/`ssh`. |
| `crypto_floss` | **N/A** | The tool uses no crypto library directly; the delegated tools (`git`, OpenSSH) are FLOSS. |
| `crypto_keylength` | **N/A** | No crypto implemented. The delegated tag-signing key is Ed25519 (meets NIST 2030 minimums), but the tool sets no key length itself. |
| `crypto_working` | **N/A** | The tool implements no crypto; the delegated signing path uses Ed25519 — no MD4/MD5/single-DES/RC4/Dual_EC_DRBG anywhere. |
| `crypto_weaknesses` | **N/A** | No crypto implemented; no SHA-1 or CBC-mode dependency exists in the codebase (delegated signing is Ed25519). |
| `crypto_pfs` | **N/A** | Implements no key-agreement protocol of its own; transport PFS, where relevant, is provided by TLS in the `git`/`gh` layer, not by this tool. Confirmed. |
| `crypto_password_storage` | **N/A** | Stores no external-user passwords; the tool holds no credentials at all. Confirmed. |
| `crypto_random` | **N/A** | The tool generates no security-relevant random values. |

## Security — delivery

| Criterion | Status | Justification / URL |
|---|---|---|
| `delivery_mitm` | **Met** | Distributed over HTTPS from GitHub — cloned and installed by symlink (`scripts/install-skill.sh`); there is no package-index artefact. Delivery integrity rides on GitHub's HTTPS transport. |
| `delivery_unsigned` | **Met** | No hash is fetched over plain HTTP. Release tags are SSH-signed and GitHub-verified. |

## Security — known vulnerabilities

| Criterion | Status | Justification / URL |
|---|---|---|
| `vulnerabilities_fixed_60_days` | **Met** | No known unpatched medium+ vulnerabilities. The runtime dependency set is the standard library only; dev/fuzz tooling is watched by Dependabot (`pip` + `github-actions` ecosystems) and OpenSSF Scorecard's Vulnerabilities check. |
| `vulnerabilities_critical_fixed` | **Met** | None have arisen — the runtime dependency graph is empty (stdlib only); any dev-tooling advisory would be handled by a Dependabot floor bump. |

## Security — other

| Criterion | Status | Justification / URL |
|---|---|---|
| `no_leaked_credentials` | **Met** | Verified: no `.env`, `.pem`, key, or credential-shaped file is tracked, and the commit history contains none. By design the tool stores no token or key (`ASSURANCE.md#4`, CWE-798/532 row). |

## Analysis — static

| Criterion | Status | Justification / URL |
|---|---|---|
| `static_analysis` | **Met** | CodeQL (`security-extended`, results uploaded to GitHub code scanning) in `.github/workflows/codeql.yml`, plus bandit-equivalent `S` rules run by `ruff check` in the CI lint job as the Python-specific second pass. |
| `static_analysis_common_vulnerabilities` | **Met** | CodeQL's `security-extended` suite targets common vulnerability classes; ruff's `S` (bandit) rules add in-line security linting on every push/PR. |
| `static_analysis_fixed` | **Met** | Findings are triaged and fixed before release. |
| `static_analysis_often` | **Met** | CodeQL runs on every push and PR to `main`, plus a weekly scheduled run. |

## Analysis — dynamic

| Criterion | Status | Justification / URL |
|---|---|---|
| `dynamic_analysis` | **Met** | An Atheris fuzz harness (`fuzz/fuzz_render.py`) exercises the renderer's token/FILL/manifest parsers; the CI `fuzz` job runs it time-boxed on every push/PR (`.github/workflows/ci.yml`). |
| `dynamic_analysis_unsafe` | **N/A** | Pure Python — memory-safe, no unsafe FFI or manual memory management. The Atheris fuzz job runs regardless. |
| `dynamic_analysis_enable_assertions` | **Met** | The suite is assertion-based and the fuzz job runs without `-O` / with `PYTHONOPTIMIZE` unset, so runtime assertions stay enabled during dynamic analysis. Confirmed. |
| `dynamic_analysis_fixed` | **Met** | No unfixed medium+ findings. |

---

## Notes

- Any passing criterion not listed here is answerable **Met** by an existing
  rendered artefact or **N/A** (library vs. website/app). Check
  `SECURITY.md` / `CONTRIBUTING.md` / `ci.yml` before writing anything new.
- Silver (score 7) is generally **not** honestly reachable while a project is
  single-maintainer: `access_continuity` is a silver MUST requiring the project to
  survive the loss of any one person within a week, and `bus_factor`,
  `governance`, and `roles_responsibilities` share that root cause. A second
  person with org access and release capability resolves all four and also moves
  Scorecard's Code-Review check off 0. See the silver sheet for how the reference
  project answered these via organisational continuity rather than a lone
  maintainer.
