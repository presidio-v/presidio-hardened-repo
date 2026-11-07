# Presidio-Hardened Toolkit: presidio-hardened-repo

## Overview

`presidio-hardened-repo` is a Claude Code skill that raises a GitHub repository to a
high [OpenSSF Scorecard](https://scorecard.dev) score and the
[OpenSSF Best Practices badge](https://www.bestpractices.dev) (passing → silver → gold).
It codifies the playbook first executed by hand for `presidio-hardened-x402`, so the
same baseline can be applied across the `presidio-hardened-*` family and beyond.

It is a **skill, not a library**: scripts, templates, playbooks and an orchestration
file (`SKILL.md`), installed by symlinking the repository into `~/.claude/skills/`. It
has no runtime dependencies and is not published to a package registry.

**Overriding rule — never over-claim.** A badge answer is an attestation. The skill
verifies and coaches; it leaves a criterion Unmet rather than fabricate a "Met" it
cannot back. Silver is the honest per-repository ceiling for a single-maintainer
project: gold's reproducible-build and second-unassociated-contributor requirements
are organisation-level programmes, not per-repository runs.

**Three kinds of work, three owners:**

| Work | Owner | Mechanism |
|---|---|---|
| Emit parameterised governance and CI files, flip GitHub settings | scripts | deterministic, idempotent |
| Honest architecture, assurance case, threat model, per-criterion answers for the target | Claude | `FILL:` markers resolved after reading the target code |
| Irreversible or outward-facing steps (make public, add collaborator, `enforce_admins`, badge registration) | human | typed GATE stops: command, consequence, rollback; one gate at a time |

## Mandatory Presidio Security Extensions

- **Fail-hard rendering:** `render.py` raises on any unresolved or undefined token
  instead of emitting a partial file.
- **FILL-marker gate:** `render.py check` reports open `FILL:` markers; `preflight.py`
  counts a file with one as UNMET.
- **Dry-run-by-default GitHub mutations:** `gh_settings.py` prints command,
  consequence and rollback and changes nothing without `--apply`; irreversible
  actions also need `--yes`.
- **No stored credentials or keys:** the tool holds no GitHub token or signing key; it
  borrows the operator's `gh` session and delegates tag signing to `git`/`ssh`.
- **Anti-leak tests:** CI checks that templates render cleanly and carry no
  example-domain content or tokens from the x402 worked example.
- **Least-privilege workflows:** emitted workflows ship `permissions: contents: read`
  and SHA-pinned actions.
- **Supply chain:** CodeQL, ruff `S` rules (bandit), OpenSSF Scorecard, a `pip-audit`
  dependency audit in CI, Dependabot, SSH-signed release tags (`allowed_signers`).

## Technical Requirements

- Python 3.11+ (`tomllib`, `datetime.UTC`); scripts are stdlib-only at run time.
- Templates: `templates/core/` (language-agnostic), `templates/python/` (overlays core
  by relative path), `templates/sheets/` (per-tier answer sheets).
- Per-target manifest `hardening.toml`, validated against `manifest.schema.json`.
- Tests with pytest; CI coverage floors at the OpenSSF gold levels (90% statement,
  80% branch); ruff lint and format; SPDX header guard.
- License MIT.

## v0.1.0 — initial release — **Delivered 2026-07-22**

Signed tag `v0.1.0`. Delivered:

- [x] `render.py` (strict renderer, `check` for tokens and FILL markers), `preflight.py`
  (MET / UNMET / NEEDS-HUMAN-EVIDENCE per criterion), `gh_settings.py` (hybrid
  dry-run / apply / `--yes`), `spdx_headers.py` (`--check` / `--apply`).
- [x] `answersheet_to_proposal.py`: a filled answer sheet becomes BadgeApp automation
  proposals, as URLs or as a committed `.bestpractices.json`.
- [x] Core and Python templates (governance, CI, Scorecard, CodeQL, publish,
  Dependabot, Atheris fuzz) and passing/silver/gold answer-sheet skeletons.
- [x] `playbook/{passing,silver,gold}.md` with human GATE blocks;
  `docs/faq-traps.md` (Scorecard URL literal match, Atheris wheels, `SCORECARD_TOKEN`,
  Signed-Releases scoring release assets rather than tags).
- [x] `docs/examples/x402/`: the original x402 artifacts as an attributed worked example.
- [x] Dogfooding: this repository hardens itself with its own templates (badge 13746,
  silver).

### Applied since (badge level, verified at bestpractices.dev on 2026-11-07)

| Repository | Badge | Level |
|---|---|---|
| presidio-hardened-x402 (origin of the playbook) | 13675 | silver |
| presidio-hardened-repo (itself) | 13746 | silver |
| presidio-hardened-ikigov-assess | 13748 | silver |
| presidio-hardened-arch-translucency | 13750 | silver |
| presidio-hardened-angellist | 13877 | silver |
| presidio-hardened-x402-mcp | 13930 | silver |
| presidio-hardened-treasury (Rust) | 15897 | silver |
| presidio-evidence | 16243 | silver |
| presidio-hardened-ai | 16301 | silver |

## Next version — planned (not yet scheduled)

Requirements drawn from the runs above. Each closes a step that is manual or fragile today.

- [ ] **Multi-tier `.bestpractices.json`.** `answersheet_to_proposal.py` takes one
  `--sheet` and writes the JSON fresh, so a silver run overwrites the passing answers.
  Accept several sheets and merge them (higher tier wins), so one file carries every
  tier the target claims.
- [ ] **Full gold coverage in `preflight.py`.** Today the gold criteria are only
  partly machine-checked.
- [ ] **Reproducible-build helper.** For hardened-ai, the release was confirmed
  reproducible by hand: wheel and sdist rebuilt from the tag matched PyPI byte for
  byte. Script that check (no `SOURCE_DATE_EPOCH`; build constraints honoured) so
  the `build_repeatable` answer is evidence, not a narrative.
- [ ] **Non-Python language layer.** Treasury (Rust) and esp32 (C / ESP-IDF) were
  hardened with hand-written CI; a `templates/rust/` layer would make that repeatable.

## Later — under evaluation

- Plugin or marketplace packaging, so the skill installs without a manual symlink
  (`docs/design.md` §Deferred: acceptable for v1).

## Open items

- `CHANGELOG.md` still lists the v0.1.0 content under `[Unreleased]`; it should be a
  dated `[0.1.0] — 2026-07-22` section at the next release.

## Version Release Checklist

At every release, before tagging: update this file (close delivered items with
"Delivered" and the date), the README roadmap, and the `SECURITY.md` supported-versions
table; then sign the tag with the `presidio-v` release key.
