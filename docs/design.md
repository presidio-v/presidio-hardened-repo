# Design

## Why this shape

The x402 hardening playbook is not "emit 11 files". The badge answer sheets prove
it is three different kinds of work, and the skill separates them because they have
different owners and different failure modes:

1. **Mechanical / deterministic** — parameterized file emission, `gh` API settings,
   labels. → **scripts** (`render.py`, `gh_settings.py`, `spdx_headers.py`).
   Idempotent and `--dry-run`-able. Prose instructions re-derived each run would
   drift; scripts don't.
2. **Judgment** — an honest `ARCHITECTURE.md` / `ASSURANCE.md` / threat model and
   per-criterion justifications *for this codebase*. → **Claude**, following
   `SKILL.md`, after reading the target. The LLM is the right engine here; a CLI
   would template-stamp dishonest boilerplate.
3. **Facts that must be true** — coverage floors, a real external reviewer, a real
   fuzz harness, an independent security review, a second unassociated contributor.
   → the skill **verifies and coaches, never fabricates** (`preflight.py`).

## Templating

- A per-target `hardening.toml` manifest is the single source of parameters (render
  input, re-run record, idempotency anchor).
- `render.py` uses `{{TOKEN}}` placeholders and **fails hard** on any unresolved or
  undefined token — no silent leftovers reach a target repo.
- Two template classes: **Class A** render-and-done (CODEOWNERS, scorecard,
  dependabot, CODE_OF_CONDUCT, allowed_signers, GOVERNANCE) and **Class B**
  skeleton + `FILL:` markers (ARCHITECTURE, ASSURANCE, SECURITY tables, CONTRIBUTING
  module list). The x402 domain prose is *stripped* from templates and kept only as
  an attributed worked example under `docs/examples/x402/`. A CI test
  (`tests/test_templates.py`) fails if any template mentions an x402-ism.

## Language layers

`templates/core/` (language-agnostic) vs `templates/python/` (ruff, pytest+coverage,
CodeQL, publish, atheris). The boundary is a directory contract, not `if` branches
inside templates — a future `rust/` layer drops in without touching core. Python
templates overlay core by relative path (the python `dependabot.yml` supersedes the
core one).

## Phasing & idempotency

Tiers `passing → silver → gold` are cumulative; the manifest's `tier` is the target
and each run does the delta. Every run works on a branch → PR (mandatory once the
two-person gate is live — even the maintainer can't self-merge), so every skill
action is itself reviewed by the gate it installs. Pre-existing target files that
diverge from the last emission are never clobbered — the divergence is surfaced in
the PR diff.

## Human gates

Enumerated, one-at-a-time, never batched: make-public, add-reviewer,
branch-protection with `enforce_admins`, org-wide 2FA, bestpractices.dev
registration, the Scorecard PAT. Each prints the exact command, the consequence,
and a rollback. `gh_settings.py` enforces this with a hybrid model: dry-run by
default, `--apply` for low-risk, `--apply --yes` for the irreversible ones.

## Verification

`preflight.py` is the source of truth: machine-checkable criteria (files + no open
FILL markers, gh API branch protection / labels / collaborator / tag verification,
coverage from `coverage.json`, literal `import atheris`, SPDX headers) report
MET/UNMET; the rest report NEEDS-HUMAN-EVIDENCE so Claude gathers evidence or leaves
them honestly Unmet. The Scorecard number comes from the `scorecard` CLI locally or
`api.scorecard.dev` after `publish_results`; the badge level from the BadgeApp JSON.

## Deferred

A plugin/marketplace wrapper. The repo is public, so external users clone and run
`scripts/install-skill.sh`; that is acceptable for v1.
