# Playbook — OpenSSF **gold** (on top of silver)

Gold requires the silver badge first. **Gold is a bigger lift than silver** and is
not "mostly documentation." Two blockers are genuinely org-level programs, not
per-repo skill runs. Do NOT mark gold criteria until they are truly closed —
over-claiming reproducible builds or a phantom second contributor is a false
attestation. Silver is the honest per-repo ceiling until the two big rocks land.

## 0. Preflight
```
python scripts/preflight.py --repo-path <repo> --tier gold
```

## A. Small config / doc actions (mostly in our control)
- `code_review_standards` + `small_tasks`: already shipped in `CONTRIBUTING.md`
  (code-review section + `good first issue` pointer) and via the `labels` command.
- `test_statement_coverage90` + `test_branch_coverage80`: the CI floors are already
  ≥90% statement / ≥80% branch. Confirm the actual numbers clear the bars; pad
  coverage with tests for error paths / optional-import fallbacks if short.
- `dynamic_analysis_enable_assertions`: the fuzz job runs Python without `-O`;
  document it in `ci.yml`.

## B. Per-file headers (mechanical)
```
python scripts/spdx_headers.py --apply src/ tests/ fuzz/ --manifest <repo>/hardening.toml
python scripts/spdx_headers.py --check src/ tests/ fuzz/        # CI guard, must pass
```
Align the `LICENSE` copyright holder to `[legal].copyright_holder`. Add the
`--check` step to the CI lint job so new files can't regress
(`copyright_per_file` + `license_per_file`).

## C. GATES

> ### GATE G1 — org-wide 2FA requirement (`require_2FA`, `secure_2FA`)
> **Org-scoped: removes any org member who does not have 2FA enabled.** Do it once
> for the whole org, and confirm every member's 2FA status FIRST.
> ```
> gh api -X PATCH orgs/<org> -f two_factor_requirement_enabled=true    # after confirming members
> ```
> Then answer `secure_2FA` (members use TOTP/WebAuthn, not SMS).

> ### GATE G2 — hardened_site headers
> Confirm HSTS / X-Content-Type-Options / CSP on the project's web properties.
> GitHub + PyPI already send them; for a library, scope the answer to those
> canonical sites, or verify any self-hosted site's headers.

## D. Real lifts (the actual gold blockers — schedule as their own work)

- **`build_reproducible`** — gold requires that *multiple parties independently
  reproduce identical builds*. Needs a deterministic wheel build
  (`SOURCE_DATE_EPOCH`, pinned build backend, normalized ordering/timestamps) AND
  at least one independent party reproducing the same artifact digest, with a
  documented procedure. Do NOT claim it until that reproduction exists.
- **`contributors_unassociated`** — gold requires *two significant contributors
  from different organizations*. A reviewer is not a contributor; the criterion
  looks at contribution history. Path: have the external reviewer (different org)
  author non-trivial merged PRs, or onboard another external contributor. This
  **cannot be faked** and gates the badge regardless of everything else.

## E. Answer sheet + verify
```
python scripts/render.py render --manifest <repo>/hardening.toml --templates templates/sheets --out <repo>/plan
python scripts/preflight.py --repo-path <repo> --tier gold
```
Fill `plan/cii-gold-answers.md` — but leave §D items Unmet with the honest note
until they are genuinely closed.
