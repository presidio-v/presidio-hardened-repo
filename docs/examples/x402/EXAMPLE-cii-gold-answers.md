---
status: working sheet (gold NOT yet achieved)
date: 2026-07-21
owner: Vladimir Stantchev
target: OpenSSF Best Practices Badge — GOLD level (project 13675, on top of silver)
project_url: https://github.com/presidio-v/presidio-hardened-x402
related:
  - plan/cii-badge-silver-answers.md
  - plan/cii-badge-passing-answers.md
---

# CII Best Practices — GOLD answer sheet (working)

Fill-in + roadmap for the **gold** tab at <https://www.bestpractices.dev/en/projects/13675>.
Covers only the criteria gold *adds* on top of silver. **Gold is a bigger lift than silver
was** — it is not "mostly documentation." Two genuine blockers remain (a second
*unassociated* contributor, and reproducible builds), plus a mechanical per-file
header pass and a handful of config/doc items.

`REPO` = `https://github.com/presidio-v/presidio-hardened-x402`.

## Current standing (2026-07-21)

- **11 gold criteria already Met** — including `two_person_review` (the review gate went
  live today: external reviewer `ceoofcyber` + CODEOWNERS + required code-owner review),
  `bus_factor`, `access_continuity`, and `security_review`.
- **~7 small config/doc actions** — mostly within our control.
- **3 real lifts** — per-file copyright/license headers (mechanical, touches every source
  file), reproducible builds, and a second unassociated significant contributor.

---

## A. Already Met — cite and move on

| Criterion | Status | Justification |
|---|---|---|
| `two_person_review` | **Met** | Every change to `main` requires an approving code-owner review from someone other than the author. Enforced by branch protection (`required_approving_review_count:1`, `require_code_owner_reviews:true`, `require_last_push_approval:true`, `dismiss_stale_reviews:true`, `enforce_admins:true`) + `REPO/blob/main/.github/CODEOWNERS` (both maintainers). External reviewer `ceoofcyber` (write collaborator) provides independent review. Live since 2026-07-21. |
| `bus_factor` | **Met** | Two members can sustain the project (maintainer `vstantch` + reviewer `ceoofcyber`), and continuity is org-backed by PRESIDIO — see `REPO/blob/main/GOVERNANCE.md#project-continuity`. |
| `access_continuity` | **Met** | Org-owned repo, OIDC Trusted Publishing (no personal token), recoverable org-held signing key, documented release flow, staffed org — `REPO/blob/main/GOVERNANCE.md#project-continuity`. |
| `security_review` | **Met** | Independent multi-round security review for v0.8.0 (2026-06-29), well within 5 years — `REPO/blob/main/SECURITY-AUDIT-2026-06-29-v0.8.0.md` and the audit history in SECURITY.md. |
| `dynamic_analysis` | **Met** | Atheris fuzzing of the canonicalisation/digest layer runs in CI on every push/PR (`REPO/blob/main/.github/workflows/ci.yml`, `fuzz/`) — applied before every release. |
| `test_statement_coverage90` | **Met** | Statement coverage **~91.6%**, gated at ≥90% in CI (gate PR #97; headroom PR #98). |
| `repo_distributed` | **Met** | git. |
| `test_invocation` | **Met** | `pytest tests/` — documented in CONTRIBUTING local-verification block. |
| `test_continuous_integration` | **Met** | CI on every push/PR across Python 3.10–3.13. |
| `hardening` | **Met** | TLS enforcement, bounded buffers, import-time log redaction, SHA-pinned Actions, digest-pinned Docker base. |
| `crypto_used_network` / `crypto_tls12` | **Met** | TLS ≥1.2 with cert verification on all egress. |

## B. Small actions — config / docs (mostly in our control)

| Criterion | Status → target | Action |
|---|---|---|
| `test_branch_coverage80` | **Met** | Branch coverage **~83.1%**, measured and gated at ≥80% in CI (gate PR #97; headroom PR #98). Per-metric enforcement in `.github/workflows/ci.yml`, `branch = true` in pyproject. |
| `code_review_standards` | **Met** — PR #97 | Documented in `CONTRIBUTING.md#code-review` (PR #97): PR-based, required non-author code-owner approval, and the checklist reviewers apply. |
| `small_tasks` | **Met** — PR #97 | `good first issue` label created; `CONTRIBUTING.md#new-to-the-project` points newcomers to it (PR #97). |
| `dynamic_analysis_enable_assertions` | **Met** — PR #97 | Fuzz job runs Python without `-O` / `PYTHONOPTIMIZE`; documented in `ci.yml` that assertions are checked during fuzzing (PR #97). |
| `require_2FA` | **Action — currently OFF** | The `presidio-v` org has `two_factor_requirement_enabled = false`. Enable "Require two-factor authentication for everyone in the organization" (Org → Settings → Authentication security). **Coordinate first** — members without 2FA are removed when it's turned on. |
| `secure_2FA` (SHOULD) | **Met-with-justification** | Members use TOTP / WebAuthn security keys, not SMS. State this once 2FA is enforced. |
| `hardened_site` | **Action — verify headers** | Confirm hardening headers (HSTS, X-Content-Type-Options, CSP where applicable) on the project sites. GitHub + PyPI already send them; check/adjust nginx on `screen.presidio-group.eu`, or scope the answer to the GitHub/PyPI canonical sites. |

## C. Real lifts — the actual gold blockers

| Criterion | Status | What it takes |
|---|---|---|
| `copyright_per_file` + `license_per_file` | **Met** (src+fuzz) — PR #99 | 2-line `SPDX-License-Identifier: MIT` + `Copyright (c) 2026 PRESIDIO Group` header on all 36 `src/`+`fuzz/` files; LICENSE holder aligned to PRESIDIO Group; CI lint job guards new files. **`tests/` headers still to add** (deferred to avoid colliding with #98; do once #98 lands). |
| `build_reproducible` | **Not met — real work** | Gold requires that **multiple parties can independently reproduce identical builds**. We currently explicitly do *not* claim reproducible builds (stated in SECURITY.md). Needs: deterministic wheel build (`SOURCE_DATE_EPOCH`, pinned build backend, normalized file ordering/timestamps) + at least one independent party reproducing the same artifact digest and a documented procedure. Non-trivial; schedule as its own task. |
| `contributors_unassociated` | **Not met — strategic blocker** | Gold requires **two significant contributors from different organizations**. `ceoofcyber` is currently a *reviewer*, not yet a code *contributor*, and the criterion looks at contribution history. Path: have `ceoofcyber` (external, different org — good) author some non-trivial merged PRs so they qualify as a significant contributor, **or** onboard another external contributor. This is the highest-effort gold item and gates the badge regardless of everything else. |

---

## Recommended sequencing

1. **Quick wins now:** enable `--cov-branch` in CI (confirm branch ≥80%), pad statement
   coverage above 90%, write the `code_review_standards` doc, add the `good first issue`
   label, document `dynamic_analysis_enable_assertions`.
2. **Coordinated config:** enable org-wide `require_2FA` (after checking all members have
   2FA), then answer `secure_2FA`; verify `hardened_site` headers.
3. **Mechanical pass:** add SPDX + copyright headers to every source file (`copyright_per_file`
   + `license_per_file`) with a CI guard.
4. **Big rocks (parallelizable, slow):** stand up `build_reproducible`; grow `ceoofcyber`
   (or another external) into a significant *contributor* for `contributors_unassociated`.

Gold is realistic but is a multi-week effort gated on (4). Silver is the honest current
ceiling until the two big rocks land.

## Notes

- Every "Met" URL under §A resolves today (silver docs merged via PR #94/#95, review gate live).
- Do not mark gold criteria until §C is genuinely closed — over-claiming reproducible builds
  or a phantom second contributor would be a false attestation on an audit-grade, patent-tied repo.
