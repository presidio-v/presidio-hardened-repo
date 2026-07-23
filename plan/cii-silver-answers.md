---
status: working sheet
owner: vstantch
target: OpenSSF Best Practices Badge — SILVER level (on top of passing)
project_url: https://github.com/presidio-v/presidio-hardened-repo
related:
  - cii-passing-answers.md
---

# CII Best Practices — SILVER answer sheet

Fill-in sheet for the **silver** tab at
<https://www.bestpractices.dev/en/projects/13746>. It covers
only the criteria silver *adds* on top of passing; passing answers carry over
unchanged (see `cii-passing-answers.md`).

This is a skeleton: rows backed by rendered project files are answered; rows that
depend on this codebase are left as `FILL` markers. Resolve every `FILL` honestly
before pasting — do not paste a marker into the BadgeApp.

Each row shows the **Status** to set in the dropdown and the **Justification** to
paste. `REPO` = `https://github.com/presidio-v/presidio-hardened-repo`.

## Badge embed — no change needed

Silver uses the **same** embed code as passing; the badge image auto-renders the
current level:

```markdown
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13746/badge)](https://www.bestpractices.dev/projects/13746)
```

If the README badge already uses this URL, it upgrades to "silver" automatically
once the badge cache refreshes — no edit required.

## Backing docs

These rendered files back the silver answers; confirm each is on `main`:

- `GOVERNANCE.md` — governance model, roles, continuity
- `ARCHITECTURE.md` — components, core flow, trust boundaries
- `ASSURANCE.md` — consolidated security assurance case (`assurance_case`)
- `allowed_signers` — public release signing key for local tag verification
- `CONTRIBUTING.md` — DCO sign-off requirement
- `SECURITY.md` — reporter credit, how to obtain signing keys, assurance-case link
- `README.md` — 12-month roadmap + links to GOVERNANCE/ARCHITECTURE/ASSURANCE

---

## Governance & continuity

| Criterion | Status | Justification to paste |
|---|---|---|
| `dco` | **Met** | Every commit must carry a DCO `Signed-off-by` line (`git commit -s`); enforced in review. Documented at `REPO/blob/main/CONTRIBUTING.md#licensing-and-developer-certificate-of-origin-dco`. Inbound = outbound `MIT`. |
| `code_of_conduct` | **Met** | Contributor Covenant at `REPO/blob/main/CODE_OF_CONDUCT.md` (standard location). |
| `governance` | **Met** | `REPO/blob/main/GOVERNANCE.md` documents the actual model — maintainer-led, single-steward (PRESIDIO Group / `presidio-v` org): rough-consensus decisions on the PR, a heightened bar for the named security-sensitive modules, SEMVER-governed API changes, and escalation to the steward org. |
| `roles_responsibilities` | **Met** | Key roles (steward org, maintainer, security contact, release manager, contributor) documented at `REPO/blob/main/GOVERNANCE.md#roles-and-responsibilities`. |
| `access_continuity` | **Met** | Continuity is a property of the steward organisation, not one person. The repository is owned by the `presidio-v` GitHub **organisation** (not a personal account), so org owners can grant repo/release access to another member at any time. There is no personal publish token to lose — the project is delivered from GitHub by symlink install, not a package index. The release signing key is held in the org password manager and is recoverable (not solely on one machine), and the signed-tag release process is documented in `SECURITY.md`. Roles are held by function within PRESIDIO Group. URL: `REPO/blob/main/GOVERNANCE.md#project-continuity`. |
| `bus_factor` (SHOULD) | **Met** | Backed by the steward org rather than a lone maintainer: PRESIDIO Group staffs more than one person able to assume the maintainer, security-contact, and release-manager roles, and release credentials (org-owned repo, recoverable signing key in the org password manager) are not tied to one individual's machine. See `REPO/blob/main/GOVERNANCE.md#project-continuity`. |

## Documentation

| Criterion | Status | Justification to paste |
|---|---|---|
| `documentation_roadmap` | **Met** | `REPO#roadmap` ("Roadmap (next 12 months)") names real near-term work: dogfood the skill to silver, then apply it to `presidio-hardened-ikigov-assess` and `-arch-translucency`; extend `preflight.py` to the full gold set; ship a reproducible-build helper; and (under evaluation) a non-Python layer and marketplace packaging. |
| `documentation_architecture` | **Met** | `REPO/blob/main/ARCHITECTURE.md` — components, core-flow pipeline, and trust boundaries; linked from the README. |
| `documentation_security` | **Met** | `SECURITY.md` documents the controls, threat model, and reporting process; `ARCHITECTURE.md#trust-boundaries` states the trust boundaries; and the consolidated four-part assurance case (threat model, trust boundaries, secure-design argument, weakness-class countermeasures) lives in `REPO/blob/main/ASSURANCE.md`. |
| `documentation_quick_start` | **Met** | README "Install" + "How it works, briefly" give the quick-start path — `scripts/install-skill.sh` to symlink the skill, then ask Claude to "harden this repo to OpenSSF silver"; `SKILL.md` documents the orchestration loop. |
| `documentation_current` | **Met** | Docs track the current release line; per-version roadmap and hand-written `CHANGELOG.md` are kept in sync with each release. |
| `documentation_achievements` | **Met** | The OpenSSF Best Practices badge is displayed and hyperlinked on the README front page. |

## Change control & reporting

| Criterion | Status | Justification to paste |
|---|---|---|
| `contribution_requirements` | **Met** | `REPO/blob/main/CONTRIBUTING.md#requirements-for-acceptable-contributions` — style, tests, security-change rules, dependency bar. |
| `report_tracker` | **Met** | GitHub Issues: `REPO/issues`. |
| `maintenance_or_update` | **Met** | `REPO/blob/main/SECURITY.md#supported-versions` states which versions are supported and for how long; `REPO/blob/main/SEMVER.md` documents the upgrade path and what counts as a breaking change. |
| `vulnerability_report_credit` | **N/A** | No vulnerabilities have been resolved in the last 12 months (zero advisories filed on this new repo), so the criterion is N/A. The crediting policy nonetheless exists at `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — reporters are credited by name in the advisory and CHANGELOG unless they request anonymity. |
| `vulnerability_response_process` | **Met** | `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — private GitHub Security Advisory intake, acknowledgement and patch targets stated. |

## Quality & testing

| Criterion | Status | Justification to paste |
|---|---|---|
| `tests_documented_added` | **Met** | `REPO/blob/main/CONTRIBUTING.md#tests` states the policy that changes adding/modifying functionality ship with tests in the same PR. |
| `test_policy_mandated` | **Met** | Formal written policy at `REPO/blob/main/CONTRIBUTING.md#tests`: functionality changes ship with tests; bug fixes include a regression test. Enforced in review and by the coverage gate. |
| `automated_integration_testing` | **Met** | `.github/workflows/ci.yml` runs the full suite on every push and pull request across a Python 3.11 / 3.12 / 3.13 matrix on `ubuntu-latest`, plus lint, SPDX guard, Atheris fuzz, and SBOM jobs. |
| `regression_tests_added50` | **Met** | Policy (`CONTRIBUTING.md#tests`) mandates a regression test with every bug fix, enforced in review and by the coverage gate. The repo is newly public with no bug-fix history yet to measure the 50% against; the policy is in force from the first fix. |
| `test_statement_coverage80` | **Met** | CI enforces `--cov-fail-under=90` (statement) in `.github/workflows/ci.yml`; the suite currently measures ~96% statement coverage over `scripts/` — well above the 80% floor. |
| `warnings_strict` | **Met** | `ruff` rule set `E, F, W, I, N, UP, S, B, A, C4, SIM, TCH` (includes the bandit-equivalent `S` security rules); only `S101`/`S603`/`S607` excluded with documented rationale (`pyproject.toml`). CI (`ci.yml` lint job) fails on any finding. |
| `coding_standards` | **Met** | `REPO/blob/main/CONTRIBUTING.md#style` names **ruff** (lint + format) as the required tool; its configuration lives in `pyproject.toml` under `[tool.ruff]` (line length 100, target `py311`, the hardened family rule set). |
| `coding_standards_enforced` | **Met** | The style/lint check runs in CI on every PR (FLOSS enforcement). |
| `installation_common` | **Met** | Installed with the standard Claude Code skill convention — `scripts/install-skill.sh` symlinks the repo into `~/.claude/skills/` (and removing the symlink uninstalls it). It is not distributed via a package index. |
| `installation_development_quick` | **Met** | `REPO/blob/main/CONTRIBUTING.md#local-verification` — documents the one setup path that installs everything needed to build and test. |
| `build_repeatable` (SHOULD) | **Met** | The runtime dependency graph is empty (standard library only), so the installed skill is trivially reproducible from source with no third-party runtime versions to vary. CI Actions are SHA-pinned. There is no lockfile because there are no runtime dependencies to pin; dev/fuzz tooling versions are not lockfile-pinned, so bit-for-bit hermetic reproducibility is not claimed. |
| `build_standard_variables` | **N/A** | Pure-Python skill with no compiler/linker step; `CC`/`CFLAGS`/`LDFLAGS` do not apply. |
| `build_preserve_debug` | **N/A** | No compiled artefacts; there is no separable debug information. |
| `build_non_recursive` | **N/A** | No recursive make or subdirectory build; the scripts run directly. |
| `installation_standard_variables` | **N/A** | Installed by symlink (`install-skill.sh`) / editable pip install; `DESTDIR`-style conventions do not apply. |

## Dependencies & components

| Criterion | Status | Justification to paste |
|---|---|---|
| `external_dependencies` | **Met** | Dependencies are listed machine-readably in `pyproject.toml` — the runtime set is empty (standard library only); the `dev` (ruff, pytest, pytest-cov) and `fuzz` (atheris) extras are declared there. A CycloneDX SBOM is generated in CI (`ci.yml` `sbom` job). There is no lockfile because there are no runtime dependencies to pin. |
| `updateable_reused_components` | **Met** | All reused components are standard package-index packages installed via the package manager (no vendored copies); Dependabot tracks updates. |
| `interfaces_current` | **Met** | Dependencies are kept current (Dependabot + dependency floors), the public API is tracked in `SEMVER.md`, and the code does not rely on deprecated FLOSS functions where alternatives exist. |

## Security

| Criterion | Status | Justification to paste |
|---|---|---|
| `assurance_case` | **Met** (URL required) | URL: `REPO/blob/main/ASSURANCE.md`. Fully written for this project (no open FILL markers): the four required parts — threat model (assets + threat/control table), trust boundaries, secure-design-principles argument, and common-implementation-weakness (CWE) countermeasures. |
| `implement_secure_design` | **Met** | Grounded in real controls (`ASSURANCE.md#3`): fail-safe defaults (`render.py` fails hard on unresolved tokens; `gh_settings.py` is dry-run until `--apply`, irreversible actions gated behind `--yes`); complete mediation (every emitted file passes `render.py check`, preflight re-checks at acceptance); least privilege (tool holds no token or key; emitted workflows ship `permissions: contents: read`); defence in depth (strict render + anti-leak test + preflight + CodeQL/ruff-S/Scorecard); economy of mechanism (stdlib-only, no bespoke crypto). |
| `input_validation` | **Met** | The untrusted inputs (the `hardening.toml` manifest and template files) are validated before use at the `manifest + templates → render.py` boundary: `render.py` raises `RenderError` on any undefined or unresolved token rather than emit a partial file, and its `check` pass blocks open FILL markers. Subprocess calls are built as argument lists (no `shell=True`). See `ARCHITECTURE.md#trust-boundaries`. |
| `hardening` | **Met** | SHA-pinned GitHub Actions across all workflows; least-privilege `permissions: contents: read` tokens (elevated only where CodeQL needs `security-events: write`); `persist-credentials: false` on checkouts; the tool stores no token or key; fail-hard rendering; and a CI anti-leak/round-trip test over the template tree. |
| `crypto_weaknesses` | **N/A** | The project implements no cryptographic mechanisms of its own; the only crypto (SSH release-tag signing) is delegated to OpenSSH using Ed25519. No MD5/SHA-1/DES is used for any security purpose anywhere in the codebase. |
| `crypto_algorithm_agility` (SHOULD) | **N/A** | No user-facing crypto-negotiation surface; the tool implements no crypto. The delegated signing algorithm (Ed25519) is a versioned choice in `allowed_signers`, not a runtime switch. |
| `crypto_credential_agility` | **Met** | No keys or secrets live in the source tree. The tool holds no credential of its own — it borrows the operator's already-authenticated `gh` session and delegates tag signing to `git`/`ssh` with the org key; every credential is external and rotatable without recompilation. Verified: no cred-shaped file is tracked. |
| `crypto_used_network` | **N/A** | The tool opens no network connection of its own. All remote calls are delegated to `gh`/`git`, which use TLS to the GitHub API. |
| `crypto_tls12` | **N/A** | No direct network client in the tool; the delegated `gh`/`git` transports enforce TLS ≥1.2. |
| `crypto_certificate_verification` | **N/A** | No direct TLS client; certificate verification is handled (and not disabled) by the delegated `gh`/`git` tools. |
| `crypto_verification_private` | **N/A** | The tool transmits no private data over its own connections; it opens none. |
| `signed_releases` | **Met** | Release tags are SSH-signed with the `presidio-v` org ed25519 key and GitHub-verified — the `v0.1.0` release tag returns `verification.verified = true` (reason `valid`). The public key is published in `REPO/blob/main/allowed_signers` (verify locally: `git -c gpg.ssh.allowedSignersFile=allowed_signers verify-tag v0.1.0`); the process is documented at `REPO/blob/main/SECURITY.md#verifying-releases-and-obtaining-public-signing-keys`. The signing key is held in the org password manager — not on GitHub, the distribution site. |
| `version_tags_signed` | **Met** | The `v0.1.0` release tag is SSH-signed with the org key and shows **Verified** on GitHub. |
| `sites_password_security` | **N/A** | The project stores no user passwords and runs no authenticating service. |

## Analysis & monitoring

| Criterion | Status | Justification to paste |
|---|---|---|
| `static_analysis_common_vulnerabilities` | **Met** | CodeQL `security-extended` (`REPO/blob/main/.github/workflows/codeql.yml`) and OpenSSF Scorecard run on every push/PR, plus the bandit-equivalent ruff `S` rules in the CI lint job. |
| `dynamic_analysis_unsafe` | **N/A** | Pure Python — memory-safe, no memory-unsafe component. An Atheris fuzz harness (`fuzz/fuzz_render.py`) runs in CI regardless. |
| `dependency_monitoring` | **Met** | Dependabot + dependency audit in CI + OpenSSF Scorecard continuously check external dependencies for known vulnerabilities. |

## Accessibility & internationalization

| Criterion | Status | Justification to paste |
|---|---|---|
| `accessibility_best_practices` | **N/A** | A developer CLI/skill with no graphical or end-user UI. |
| `internationalization` | **N/A** | No user-facing localizable UI strings; output is developer-facing English CLI text. |

---

## Notes

- Any silver criterion **not** listed here carries over unchanged from the passing
  sheet — leave those answers as they already are.
- If BadgeApp shows a silver-only criterion not covered above, it is almost
  certainly answerable **N/A** (library vs. website/app) or **Met** by an existing
  artefact; check `SECURITY.md` / `CONTRIBUTING.md` / `ci.yml` first.
- `bus_factor`, `build_repeatable`, and `crypto_algorithm_agility` are SHOULD
  criteria — "Met" / "N/A" with an honest justification is accepted; none is a
  hard blocker.
- `assurance_case` is the only silver MUST that requires a net-new document
  (`ASSURANCE.md`); resolve its own FILL markers before answering this row.
