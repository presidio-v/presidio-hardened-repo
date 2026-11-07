# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Changes on `main` since the v0.1.0 tag, mostly fixes found while applying the skill to
other repositories (ikigov-assess, arch-translucency, treasury, evidence, hardened-ai).

### Added
- `PRESIDIO-REQ.md`: requirements baseline, the v0.1.0 delivery record, the
  repositories hardened since, and the planned next items (#14).
- `answersheet_to_proposal.py --bestpractices-json PATH`: writes a `.bestpractices.json`
  the BadgeApp reads from the target repo, avoiding URL length limits and concurrent
  form saves (#3).
- `preflight.py`: a "Workflow hardening (Scorecard)" group that flags a target's
  existing workflows without a top-level `permissions:` block or with unpinned
  `uses:`, and a remote `SCORECARD_TOKEN` secret check (#4).
- Signed source archives for source-only targets: `allowed_signers.tmpl` allows the
  release key for the `file` namespace as well as `git`, `SECURITY.md.tmpl` documents
  archive verification, and `docs/faq-traps.md` / `playbook/silver.md` note that
  Scorecard's Signed-Releases check scores release assets, not tags (#11).
- A `pip-audit` dependency-audit job in CI, and the SDLC tier statement in
  `SECURITY.md` (#13).

### Changed
- `SKILL.md`: new step 4 "Harden existing workflows" (with the SHA-pinning recipe),
  a `SCORECARD_TOKEN` step, and step 7 now prefers `--bestpractices-json` (#4).
- `answersheet_to_proposal.py`: default `--max-url-len` 6000 → 7000, a warning to open
  multiple URLs one at a time (#3), and the sheet's `REPO` shorthand expanded to the
  real repository URL (#4).
- `preflight.py`: any test workflow counts for continuous integration, not only
  `ci.yml`; criteria are scoped to the requested tier, so gold-only items no longer
  show UNMET at passing or silver (#3).
- Templates: the coverage floor in `CONTRIBUTING.md.tmpl` and the SAST claim in
  `ASSURANCE.md.tmpl` are `FILL:` markers instead of hard-coded text (#3).
- README: states the SDLC tier and links the applicability matrix (#5, #7); the
  roadmap reflects the work done (#14). Dependabot groups GitHub Actions updates (#8).

### Fixed
- `fuzz/*` is exempt from ruff's naming rules that Atheris' `TestOneInput` breaks,
  which had left lint red (#4).

## [0.1.0] — 2026-07-22

### Added
- Initial `presidio-hardened-repo` skill: a repeatable OpenSSF hardening playbook
  generalized from `presidio-hardened-x402`.
- `scripts/render.py` — strict template renderer (fails hard on unresolved tokens;
  tracks `FILL:` judgment markers).
- `scripts/preflight.py` — per-criterion gap analysis / acceptance checker.
- `scripts/gh_settings.py` — GitHub-side settings under a hybrid dry-run/apply/--yes
  safety model; Scorecard is left out of the discovered required status checks (#2).
- `scripts/spdx_headers.py` — per-file SPDX + copyright header insertion/verification.
- `scripts/answersheet_to_proposal.py` — a filled answer sheet becomes BadgeApp
  automation proposal URLs.
- `templates/core/` and `templates/python/` — parameterized governance, CI,
  Scorecard, CodeQL, publish, dependabot, and Atheris fuzz templates.
- `templates/sheets/` — passing/silver/gold bestpractices.dev answer-sheet skeletons.
- `playbook/{passing,silver,gold}.md` — ordered steps with human GATE blocks.
- `docs/examples/x402/` — the original x402 artifacts as an attributed worked example.
