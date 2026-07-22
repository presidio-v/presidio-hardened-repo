---
status: SILVER ACHIEVED 2026-07-21
date: 2026-07-21
owner: Vladimir Stantchev
target: OpenSSF Best Practices Badge — SILVER level (project 13675, on top of passing)
project_url: https://github.com/presidio-v/presidio-hardened-x402
related:
  - plan/cii-badge-passing-answers.md
---

# CII Best Practices — SILVER answer sheet

**Status: silver badge awarded 2026-07-21** (confirmation from badgeapp@bestpractices.dev,
"CONGRATULATIONS on achieving a silver best practices badge!"). This sheet is the record of
the answers submitted for the **silver** tab at
<https://www.bestpractices.dev/en/projects/13675>. It covers only the criteria silver *adds*
on top of passing; passing answers carry over unchanged (see `plan/cii-badge-passing-answers.md`).

Each row shows the **Status** set in the dropdown and the **Justification** pasted into the
text box. `REPO` = `https://github.com/presidio-v/presidio-hardened-x402`.

## Badge embed — no change needed

The silver award uses the **same** embed code as passing; the badge image auto-renders the
current level:

```markdown
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13675/badge)](https://www.bestpractices.dev/projects/13675)
```

The README badge added in PR #90 already uses this URL, so it upgrades to "silver"
automatically once the badge cache refreshes — no edit required.

## Backing docs (PR #94 → `main`)

Seven files back these answers, shipped on branch `docs/openssf-silver` (PR #94):

- **new** `GOVERNANCE.md` — governance model, roles, continuity
- **new** `ARCHITECTURE.md` — components, payment flow, trust boundaries
- **new** `ASSURANCE.md` — consolidated security assurance case (`assurance_case`)
- **new** `allowed_signers` — public release signing key for local tag verification
- **edit** `CONTRIBUTING.md` — DCO sign-off requirement
- **edit** `SECURITY.md` — reporter credit, how to obtain signing keys, assurance-case link
- **edit** `README.md` — 12-month roadmap + links to GOVERNANCE/ARCHITECTURE/ASSURANCE

---

## Governance & continuity

| Criterion | Status | Justification to paste |
|---|---|---|
| `dco` | **Met** | Every commit must carry a DCO `Signed-off-by` line (`git commit -s`); enforced in review. Documented at `REPO/blob/main/CONTRIBUTING.md#licensing-and-developer-certificate-of-origin-dco`. Inbound = outbound MIT. |
| `code_of_conduct` | **Met** | Contributor Covenant at `REPO/blob/main/CODE_OF_CONDUCT.md` (standard location). |
| `governance` | **Met** | Maintainer-led single-steward model documented at `REPO/blob/main/GOVERNANCE.md` — decision-making, escalation to PRESIDIO, and security/API change rules. |
| `roles_responsibilities` | **Met** | Key roles (steward org, maintainer, security contact, release manager, contributor) documented at `REPO/blob/main/GOVERNANCE.md#roles-and-responsibilities`. |
| `access_continuity` | **Met** | See `REPO/blob/main/GOVERNANCE.md#project-continuity`. Continuity is a property of the steward organisation, not one person: the repo is owned by the `presidio-v` GitHub org (not a personal account); PyPI publishing uses GitHub Trusted Publishing (OIDC) bound to the org repo + a gated `release` environment, so there is no personal token that dies with an individual; the release signing key is held in the organisation password manager (custody with PRESIDIO leadership) and is recoverable; the release process is fully documented; and PRESIDIO is a staffed organisation with more than one person able to assume each role. Issue triage, change acceptance, and releases can therefore continue within one week if any single individual becomes unavailable. |
| `bus_factor` | **Met** | Bus factor is backed by the PRESIDIO organisation rather than a lone maintainer: more than one person can assume the maintainer, security-contact, and release-manager roles, and all release credentials are org-held and recoverable (not tied to one machine). See `REPO/blob/main/GOVERNANCE.md#project-continuity`. |

## Documentation

| Criterion | Status | Justification to paste |
|---|---|---|
| `documentation_roadmap` | **Met** | `REPO#roadmap` includes a "Planned direction (next 12 months)" section covering intended work: toward v1.0 / mainnet gate, prompt-injection scanning (#23), broader rail coverage, and evidence/conformance growth. |
| `documentation_architecture` | **Met** | `REPO/blob/main/ARCHITECTURE.md` — components, payment-flow pipeline, and trust boundaries; linked from the README. |
| `documentation_security` | **Met** | `REPO/blob/main/SECURITY.md` documents the security controls, per-version threat model, and reporting process; `ARCHITECTURE.md#trust-boundaries` states the trust boundaries; `REPO/blob/main/PRESIDIO-REQ.md` carries the full threat model and design rationale. |
| `documentation_quick_start` | **Met** | README "Quick Start" (before/after example) plus `docs/quickstarts/` (Coinbase CDP, LangChain, CrewAI). |
| `documentation_current` | **Met** | Docs track the current release line (v0.9.x); per-version roadmap and hand-written `CHANGELOG.md` are kept in sync with each release. |
| `documentation_achievements` | **Met** | The OpenSSF Best Practices badge is displayed and hyperlinked on the README front page (added in PR #90). |

## Change control & reporting

| Criterion | Status | Justification to paste |
|---|---|---|
| `contribution_requirements` | **Met** | `REPO/blob/main/CONTRIBUTING.md#requirements-for-acceptable-contributions` — style, tests, security-change rules, dependency bar. |
| `report_tracker` | **Met** | GitHub Issues: `REPO/issues`. |
| `maintenance_or_update` | **Met** | `REPO/blob/main/SECURITY.md#supported-versions` states which versions are supported and for how long; `REPO/blob/main/SEMVER.md` documents the upgrade path and what counts as a breaking change. |
| `vulnerability_report_credit` | **Met** | `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — reporters are credited by name in the published advisory and the CHANGELOG entry unless they request anonymity. |
| `vulnerability_response_process` | **Met** | `REPO/blob/main/SECURITY.md#reporting-a-vulnerability` — private GitHub Security Advisory intake, acknowledgement within 5 business days, patch target within 30 days. |

## Quality & testing

| Criterion | Status | Justification to paste |
|---|---|---|
| `tests_documented_added` | **Met** | `REPO/blob/main/CONTRIBUTING.md#tests` states the policy that changes adding/modifying functionality ship with tests in the same PR. |
| `test_policy_mandated` | **Met** | Formal written policy at `REPO/blob/main/CONTRIBUTING.md#tests`: "any change that adds or modifies functionality must ship with tests… Bug fixes must include a regression test." Enforced in review and by the coverage gate. |
| `automated_integration_testing` | **Met** | `REPO/blob/main/.github/workflows/ci.yml` runs the full suite on every push and pull request (Python 3.10–3.13) plus the partner conformance suite. |
| `regression_tests_added50` | **Met** | Policy requires a regression test with every bug fix; e.g. the replay-fingerprint precision collision fix (PR #89) added a `TestCanonicalAmount` class and a high-precision collision regression test. Well over 50% of bugs fixed in the last 6 months have regression tests. |
| `test_statement_coverage80` | **Met** | CI enforces `--cov-fail-under=90` (see `ci.yml` and `pyproject.toml [tool.coverage.report]`), so statement coverage is ≥90%, above the 80% bar. |
| `warnings_strict` | **Met** | ruff runs with rule sets `E,F,W,I,N,UP,S,B,A,C4,SIM,TCH` (including bandit `S` security rules); CI fails on any finding, i.e. warnings are treated as errors. |
| `coding_standards` | **Met** | `REPO/blob/main/CONTRIBUTING.md#style` names ruff as the required style/lint tool; config in `pyproject.toml`. |
| `coding_standards_enforced` | **Met** | `ruff check` and `ruff format --check` run in CI on every PR (FLOSS enforcement). |
| `installation_common` | **Met** | Standard install from PyPI: `pip install presidio-hardened-x402` (also `uv`). |
| `installation_development_quick` | **Met** | `REPO/blob/main/CONTRIBUTING.md#local-verification` — `python -m venv .venv && .venv/bin/pip install -e ".[dev]"` installs everything needed to build and test. |
| `build_repeatable` | **Met (SHOULD)** | Wheels/sdists are built via the standard PEP 517 flow against a fully pinned dependency graph (`uv.lock`) on GitHub-hosted runners with SHA-pinned Actions. We do not yet claim bit-for-bit reproducible/hermetic builds — that is a stretch target beyond the SLSA L3 baseline we ship — but the build is deterministic from pinned sources. |
| `build_standard_variables` | **N/A** | Pure-Python package; no compiler/linker, so `CC`/`CFLAGS`/`LDFLAGS` do not apply. |
| `build_preserve_debug` | **N/A** | Pure Python; no compiled artefacts, so there is no separable debug information. |
| `build_non_recursive` | **N/A** | No recursive make/subdirectory build. |
| `installation_standard_variables` | **N/A** | Installed via pip/uv into a Python environment; `DESTDIR`-style conventions do not apply. |

## Dependencies & components

| Criterion | Status | Justification to paste |
|---|---|---|
| `external_dependencies` | **Met** | Dependencies are listed machine-readably in `REPO/blob/main/pyproject.toml` and fully pinned in `uv.lock`; a CycloneDX SBOM is generated per release in CI. |
| `updateable_reused_components` | **Met** | All reused components are standard PyPI packages installed via pip/uv (no vendored copies); Dependabot tracks updates. |
| `interfaces_current` | **Met** | Dependencies are kept current (Dependabot + dependency floors), the public API is tracked in `SEMVER.md`, and the code does not rely on deprecated FLOSS functions where alternatives exist. |

## Security

| Criterion | Status | Justification to paste |
|---|---|---|
| `assurance_case` | **Met** (URL required) | URL: `REPO/blob/main/ASSURANCE.md`. Consolidated assurance case with all four required parts: (1) threat model — assets, adversaries (compromised/overspending agent, replay, spoofed SLO trigger, audit tampering, metadata leakage) + mitigations (per-version tables in SECURITY.md, full rationale in PRESIDIO-REQ.md); (2) trust boundaries (agent→library untrusted input, library→chain irreversible egress, network egress to screening/audit, out-of-scope signing-key custody); (3) secure-design-principles argument (fail-safe defaults, complete mediation, least privilege, defence in depth, economy of mechanism); (4) common-implementation-weakness argument (input validation/injection, memory safety, crypto misuse, hard-coded secrets, insecure network/SSRF, replay, audit tampering, unsafe deserialization, vulnerable deps — each mapped to a control and to CodeQL/bandit/Scorecard + the independent v0.8.0 review). |
| `implement_secure_design` | **Met** | The library applies secure design principles: fail-safe defaults / secure by default (fail-closed pipeline, redact-by-default PII), complete mediation (policy + replay + PII before egress), least privilege (never holds wallet keys — `PaymentSigner` is abstract), defence in depth (independent policy / replay / PII / MPA / HMAC-chained audit / signed-evidence controls, plus SLO-broker cooldowns and caps), and economy of mechanism (vetted `hashlib`/`hmac`/`secrets`/`cryptography` primitives — SHA-256, HMAC-SHA256, ed25519 — no bespoke crypto). See `REPO/blob/main/ARCHITECTURE.md` and `REPO/blob/main/SECURITY.md`. |
| `input_validation` | **Met** | All payment metadata arriving from the calling agent is treated as untrusted and validated before use (e.g. `action_ref` rejects empty entity-type sets; canonicalisation enforces byte-stability contracts). See `ARCHITECTURE.md#trust-boundaries`. |
| `hardening` | **Met** | TLS enforced on all network egress; bounded audit buffers; import-time log redaction of secrets; SHA-pinned GitHub Actions; digest-pinned Docker base and hash-pinned spaCy model. |
| `crypto_weaknesses` | **Met** | Security functions use SHA-256 / HMAC-SHA256 / ed25519 only; no MD5, SHA-1, or DES for security purposes. |
| `crypto_algorithm_agility` (SHOULD) | **N/A** | The library exposes no user-facing crypto-algorithm negotiation surface; integrity/signature primitives are pinned to current strong choices (SHA-256, HMAC-SHA256, ed25519). Algorithm migration is handled at the record-format layer instead — emitted records are explicitly versioned (`payment-decision@1`, `evidence-ref@1`, `capability-grant@1`) and canonicalisation/digest functions are byte-stability contracts, so replacing an algorithm is a versioned format change, not a runtime switch. Runtime crypto-suite negotiation does not apply to this library's design. (Alternatively defensible as Unmet-with-this-justification; it is a SHOULD.) |
| `crypto_credential_agility` | **Met** | All keys/secrets are supplied from outside the source tree and are rotatable without recompilation: the replay-fingerprint and audit-chain keys come from env vars (`PRESIDIO_X402_FINGERPRINT_KEY`, `PRESIDIO_X402_CHAIN_KEY`); evidence-signing keys and trust stores are deployment-supplied separate files/config; none are hard-coded, none sit in the non-secret config, and `install_log_redaction()` scrubs key/token material from logs. |
| `crypto_used_network` | **Met** | Network communication to the hosted screening service and remote audit sinks uses TLS. |
| `crypto_tls12` | **Met** | The hardened HTTP client (reused from `presidio-hardened-requests`) uses TLS ≥1.2. |
| `crypto_certificate_verification` | **Met** | TLS certificate verification is on by default; the client does not disable verification. |
| `crypto_verification_private` | **Met** | Certificate verification precedes transmission of any private data; on remote failure the local regex backstop keeps the flow fail-safe. |
| `signed_releases` | **Met** | Releases are cryptographically signed and the process for obtaining/verifying keys is documented at `REPO/blob/main/SECURITY.md#obtaining-the-public-signing-keys`: Sigstore build provenance (`gh attestation verify`), SSH-signed git tags with the public key in `REPO/blob/main/allowed_signers`, and PEP 740 attestations on PyPI. |
| `version_tags_signed` | **Met** | Every release is a git tag, SSH-signed with the org key and shown as Verified on GitHub. |
| `sites_password_security` | **N/A** | The library stores no user passwords. |

## Analysis & monitoring

| Criterion | Status | Justification to paste |
|---|---|---|
| `static_analysis_common_vulnerabilities` | **Met** | CodeQL (`REPO/blob/main/.github/workflows/codeql.yml`), bandit via ruff `S` rules, and OpenSSF Scorecard run on every push/PR. |
| `dynamic_analysis_unsafe` | **N/A** | Pure Python is memory-safe; there is no memory-unsafe-language component. (Atheris fuzzing of the canonicalisation/digest layer runs in CI regardless.) |
| `dependency_monitoring` | **Met** | Dependabot + `pip-audit` in CI + OpenSSF Scorecard continuously check external dependencies for known vulnerabilities. |

## Accessibility & internationalization

| Criterion | Status | Justification to paste |
|---|---|---|
| `accessibility_best_practices` | **N/A** | Developer library with no graphical or end-user UI — there is no user interface to make accessible. |
| `internationalization` | **N/A** | The library processes structured/byte payment data, not localizable UI strings; PII handling is Unicode-aware (NFC normalization). There is no user-facing interface requiring localization. |

---

## Notes

- Any silver criterion **not** listed here is one that carries over unchanged from the
  passing sheet — leave those answers as they already are.
- If the BadgeApp shows a silver-only criterion not covered above, it is almost certainly
  answerable **N/A** (library vs. website/app) or **Met** by an existing artefact; check
  `SECURITY.md` / `CONTRIBUTING.md` / `ci.yml` before writing anything new.
- `bus_factor`, `build_repeatable`, and `crypto_algorithm_agility` are SHOULD criteria —
  "Met" / "N/A" with the justification above is accepted; none is a hard blocker.
- `assurance_case` is the only silver MUST that required a net-new document (`ASSURANCE.md`);
  everything else was existing engineering or a small doc edit.