---
name: presidio-hardened-repo
description: >-
  Harden a GitHub repository to a high OpenSSF Scorecard score and earn the
  OpenSSF Best Practices badge (passing -> silver -> gold). Applies the repeatable
  playbook from presidio-hardened-x402: governance/security docs, CI + Scorecard +
  CodeQL workflows, dependency and SBOM automation, signed releases, a two-person
  review gate, and honest per-criterion answer sheets. Use when asked to "harden
  this repo", "get the OpenSSF badge", "raise our Scorecard score", "add
  governance/security docs", or to onboard a presidio-v repo to the family
  security baseline. Python-first; core layer is language-agnostic.
---

# presidio-hardened-repo

A skill that takes a GitHub repo (public or private) and raises it to a high
OpenSSF Scorecard score and an OpenSSF Best Practices badge, by applying the exact
playbook that was executed by hand for `presidio-hardened-x402`.

## The one rule that overrides everything

**Never over-claim. The skill verifies and coaches; it never fabricates.** A
badge answer or a criterion status is an *attestation*. On audit-grade,
patent-tied repos a false "Met" is worse than an honest "Unmet". If a fact is not
true yet (coverage below the floor, no real external reviewer, no independent
security review, no second unassociated contributor), the skill leaves it Unmet
and tells the human what it would take — it does not paper over it. This rule is
inherited from the x402 gold sheet and is non-negotiable.

## What the work actually is (three kinds)

1. **Mechanical** — render parameterized files, flip `gh` API settings, add
   labels. Done by the scripts. Deterministic and idempotent.
2. **Judgment** — write an *honest* ARCHITECTURE / ASSURANCE / threat model and
   per-criterion justifications *for this codebase*. Done by you (Claude) after
   reading the target repo. Templates leave `<!-- FILL:slug -->` markers exactly
   where judgment is required; a phase is not complete while any survive.
3. **Human-gated** — irreversible or outward-facing steps (make repo public, add a
   collaborator, `enforce_admins` branch protection, org-wide 2FA, register at
   bestpractices.dev). The skill STOPS at each gate with the exact command, the
   consequence, and a rollback note. It never batches two gates.

## Tiers

Ordered, cumulative: `passing` -> `silver` -> `gold`. Silver requires passing
first; gold requires silver first. The target tier is `[project].tier` in the
manifest. Re-running with a higher tier only does the delta. **Silver is the
honest per-repo ceiling** for a single-maintainer project — gold's two big rocks
(reproducible builds, a second *unassociated* contributor) are org-level programs,
not per-repo skill runs.

## Inputs: the manifest

Each target repo gets a `hardening.toml` at its root (schema:
`manifest.schema.json`). It is the render input, the re-run record, and the
idempotency anchor. Copy `hardening.toml` from this repo as the template and edit
it. Fields: see the schema; the human decisions are `[people].reviewer` (the
external two-person-review gate) and `[project].tier`.

## Scripts (this repo's `scripts/`)

- `render.py render --manifest hardening.toml --templates templates/core --out <repo>`
  — fill templates. Fails hard on any unresolved token. Also renders
  `templates/python` for `language = "python"` targets (python files overlay core
  by relative path, so the python `dependabot.yml` supersedes the core one).
- `render.py check <path>` — report unresolved tokens and open FILL markers under
  a path. A phase is done only when this is clean for the emitted files.
- `preflight.py --repo-path <repo> --tier <t>` — gap analysis + acceptance.
  Prints MET / UNMET / NEEDS-HUMAN-EVIDENCE per criterion. Run it first (to see
  the gaps) and last (to confirm). It is a report, not a gate (`--strict` to fail
  on UNMET).
- `gh_settings.py <subcommand> --repo <slug>` — GitHub-side settings. **Hybrid
  safety**: every mutation is dry-run by default (prints the exact command +
  consequence + rollback); `--apply` executes low-risk ones; HIGH-risk
  (`make-public`, `add-reviewer`, `branch-protection`) also require `--yes`.
- `spdx_headers.py --check|--apply <paths>` — gold per-file SPDX + copyright
  headers; `--check` is the CI guard.

## How to run (the orchestration loop)

For a target repo, follow the tier playbook in `playbook/<tier>.md`. In outline:

1. **Preflight.** `preflight.py --repo-path <repo> --tier <tier>` → the gap list.
   Read the target codebase enough to do the judgment work honestly.
2. **Manifest.** Create/confirm the target's `hardening.toml`.
3. **Emit.** `render.py render` the core (and python) templates on a *branch*,
   never to main directly. Then run `render.py check` — while FILL markers remain,
   **you** write the missing prose (threat model, architecture components,
   security-sensitive modules, per-criterion justifications) by reading the target
   code. Re-run `check` until clean.
4. **Idempotency.** If a target file already exists and diverges from what the
   skill last emitted, do NOT clobber it — surface the divergence in the PR diff
   and merge by hand. (`hardening.lock.json` records emission digests; if absent,
   treat any pre-existing file as human-owned and diff against it.)
5. **Config gates.** Walk the GATE blocks in the playbook one at a time. For each,
   present the `gh_settings.py` dry-run, get an explicit human go, then `--apply`
   (+ `--yes` for HIGH). Low-risk config (labels, security features) can be applied
   together; gates cannot.
6. **Answer sheet.** Render `templates/sheets/cii-<tier>-answers.md.tmpl` into the
   target's `plan/`, fill the FILL markers honestly from the evidence, and hand it
   to the human to transcribe at bestpractices.dev. Register the project URL
   EXACTLY as `https://github.com/<org>/<repo>` (Scorecard does a literal match).
7. **Verify.** Re-run `preflight.py`; run Scorecard locally (or wait for the
   weekly action) and poll `api.scorecard.dev`. Confirm the badge level via
   `https://www.bestpractices.dev/projects/<id>.json`.

## Traps (see `docs/faq-traps.md`)

- bestpractices.dev URL must be a literal `https://github.com/<org>/<repo>` — no
  trailing slash, no `www.`, not the PyPI URL, or Scorecard's CII check reads 0.
- Scorecard's Fuzzing check greps for the literal string `import atheris`; it does
  **not** detect Hypothesis. Keep that literal line in the fuzz harness.
- Atheris has no macOS wheel and no cp310 wheel — fuzz job runs on Linux under 3.12.
- Scorecard's Branch-Protection check needs a fine-grained PAT (`admin:read`) as
  `SCORECARD_TOKEN`; the default `GITHUB_TOKEN` cannot read protection rules.
- Code-Review scores 0 for a single-contributor project — this is why the
  external reviewer / two-person gate is the highest-leverage single change.

## Layout

- `templates/core/` — language-agnostic governance, scorecard, CODEOWNERS.
- `templates/python/` — ruff, pytest+coverage floors, CodeQL, publish, atheris.
- `templates/sheets/` — per-tier answer-sheet skeletons.
- `playbook/{passing,silver,gold}.md` — ordered steps with GATE blocks.
- `scripts/` — render, preflight, gh_settings, spdx_headers.
- `docs/examples/x402/` — the real x402 artifacts, as an attributed worked example
  (NOT templates — do not copy their domain content into a target).

This repo hardens itself with its own templates (dogfooding); its `hardening.toml`
targets silver.
