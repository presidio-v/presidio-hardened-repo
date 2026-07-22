# Playbook — OpenSSF **silver** (on top of passing)

Silver requires the passing badge first. It is *mostly documentation plus one
net-new document* (`ASSURANCE.md`) plus the two-person review gate — but each doc
must be honest for this codebase. Work on a branch → PR.

## 0. Preflight
```
python scripts/preflight.py --repo-path <repo> --tier silver
```

## 1. Manifest
Set `[project].tier = "silver"`. Confirm `[people].reviewer` is a real external
handle (for the presidio family this is `ceoofcyber`).

## 2. Emit the silver governance layer (branch)
Re-run the core render (it now emits/updates the silver docs). Silver adds:
- `GOVERNANCE.md` — governance model, roles, **project continuity** (this is what
  makes `access_continuity` and `bus_factor` honest: org-owned repo, OIDC Trusted
  Publishing, org-held recoverable signing key, documented release flow, staffed org).
- `CODE_OF_CONDUCT.md` — Contributor Covenant.
- `ARCHITECTURE.md` — components, processing flow, **trust boundaries**.
- `ASSURANCE.md` — the consolidated assurance case (the one silver MUST that needs
  a net-new doc).
- `SEMVER.md`, `allowed_signers`.
- `CONTRIBUTING.md` gains DCO sign-off; `SECURITY.md` gains reporter credit + how
  to obtain signing keys + assurance-case link; `README` gains the 12-month roadmap.
```
python scripts/render.py check <repo>     # drive FILL markers to zero
```

## 3. Judgment work (you, Claude — the heart of silver)
Resolve, honestly, from the target code:
- `ARCHITECTURE.md`: `FILL:components`, `FILL:processing-flow`, `FILL:trust-boundaries`.
- `ASSURANCE.md`: all four parts — `FILL:threat-model`, `FILL:trust-boundaries`,
  `FILL:secure-design-argument`, `FILL:weakness-argument`. Map each weakness class
  to a real control and to CodeQL/bandit/Scorecard. If a control is absent, say
  so; do not claim defence you don't have.
- `GOVERNANCE.md`: `FILL:security-sensitive-areas`.
- `SECURITY.md`: supported-versions and threat tables.

## 4. Silver quality bar (mostly already true from passing)
- `test_statement_coverage80`: the CI gate is already ≥90%. ✓
- `dependency_monitoring`: Dependabot + `pip-audit` in CI. ✓
- `signed_releases` + `version_tags_signed`: SSH-signed tags with `allowed_signers`;
  document key-obtaining in `SECURITY.md`. Confirm the release flow actually signs.

## 5. GATES — the two-person review gate (the leverage item)

> ### GATE S1 — add the external reviewer as a write collaborator
> Grants write access to an audit-grade repo. Trust decision — human confirms.
> ```
> python scripts/gh_settings.py add-reviewer --repo <org>/<repo> --user <reviewer>          # dry-run
> python scripts/gh_settings.py add-reviewer --repo <org>/<repo> --user <reviewer> --apply --yes
> ```
> Then confirm `.github/CODEOWNERS` lists `@<maintainer> @<reviewer>` (emitted in step 2).

> ### GATE S2 — required review + code-owner review + enforce_admins on main
> **Can lock the maintainer out of their own `main`** — every change, including the
> maintainer's, then needs the reviewer's approval (no self-merge). This is exactly
> what earns Scorecard Code-Review and Branch-Protection and the silver review
> criteria.
> ```
> python scripts/gh_settings.py branch-protection --repo <org>/<repo>            # dry-run: shows the PATCH
> python scripts/gh_settings.py branch-protection --repo <org>/<repo> --apply --yes
> ```
> Rollback: `gh api -X DELETE repos/<org>/<repo>/branches/main/protection` (admin).

## 6. Answer sheet
```
python scripts/render.py render --manifest <repo>/hardening.toml --templates templates/sheets --out <repo>/plan
```
Fill `plan/cii-silver-answers.md` honestly. Confirm the honest N/A defaults
(crypto_pfs, accessibility/i18n for a library, password storage) actually apply.
Then generate a click-to-propose URL so the human reviews/accepts the silver
answers instead of hand-entering them (unforced by default — existing answers are
untouched unless `--overrides` is passed):
```
python scripts/answersheet_to_proposal.py --sheet <repo>/plan/cii-silver-answers.md --repo-path <repo>
```
Submit the silver tab at `bestpractices.dev/projects/<id>`.

## 7. Verify
```
python scripts/preflight.py --repo-path <repo> --tier silver
```
The badge embed URL is unchanged; the image auto-renders "silver" once the
BadgeApp cache refreshes. Poll `bestpractices.dev/projects/<id>.json`.
