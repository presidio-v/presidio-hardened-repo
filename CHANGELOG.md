# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial `presidio-hardened-repo` skill: a repeatable OpenSSF hardening playbook
  generalized from `presidio-hardened-x402`.
- `scripts/render.py` — strict template renderer (fails hard on unresolved tokens;
  tracks `FILL:` judgment markers).
- `scripts/preflight.py` — per-criterion gap analysis / acceptance checker.
- `scripts/gh_settings.py` — GitHub-side settings under a hybrid dry-run/apply/--yes
  safety model.
- `scripts/spdx_headers.py` — per-file SPDX + copyright header insertion/verification.
- `templates/core/` and `templates/python/` — parameterized governance, CI,
  Scorecard, CodeQL, publish, dependabot, and Atheris fuzz templates.
- `templates/sheets/` — passing/silver/gold bestpractices.dev answer-sheet skeletons.
- `playbook/{passing,silver,gold}.md` — ordered steps with human GATE blocks.
- `docs/examples/x402/` — the original x402 artifacts as an attributed worked example.
