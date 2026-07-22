# presidio-hardened-repo

[![CI](https://github.com/presidio-v/presidio-hardened-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/presidio-v/presidio-hardened-repo/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/presidio-v/presidio-hardened-repo/badge)](https://scorecard.dev/viewer/?uri=github.com/presidio-v/presidio-hardened-repo)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/0/badge)](https://www.bestpractices.dev/projects/0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- The Best Practices badge points at project 0 until this repo is registered
     at bestpractices.dev; set badge.bestpractices_id in hardening.toml then. -->


A Claude Code skill that takes a GitHub repository — public or private — and
raises it to a high [OpenSSF Scorecard](https://scorecard.dev) score and earns the
[OpenSSF Best Practices badge](https://www.bestpractices.dev)
(**passing → silver → gold**). It codifies the exact playbook that was executed by
hand for `presidio-hardened-x402` so it can be re-applied across the
`presidio-hardened-*` family and beyond.

## What it does

Three kinds of work, handled differently:

| Work | Owner | Mechanism |
|---|---|---|
| Emit parameterized governance/CI files; flip `gh` settings; add labels | scripts | deterministic, idempotent |
| Write an *honest* architecture / assurance case / threat model / per-criterion justification for **this** codebase | Claude | `FILL:` markers resolved after reading the target repo |
| Irreversible / outward-facing steps (make public, add collaborator, `enforce_admins`, org 2FA, badge registration) | human | typed GATE stops with command + consequence + rollback |

**One overriding rule: never over-claim.** A badge answer is an attestation. The
skill verifies and coaches; it never fabricates a "Met" it cannot back.

## Install

```
scripts/install-skill.sh      # symlinks this repo into ~/.claude/skills/
```
Then, in a repo you want to harden, ask Claude to "harden this repo to OpenSSF
silver" (or invoke the skill). See `SKILL.md` for the orchestration loop.

## Layout

```
SKILL.md                     orchestrator: phases, gates, the no-over-claim rule
hardening.toml               this repo's own manifest (dogfoods itself → silver)
manifest.schema.json         the per-target manifest schema
templates/core/              language-agnostic governance + scorecard + CODEOWNERS
templates/python/            ruff, pytest+coverage floors, CodeQL, publish, atheris
templates/sheets/            per-tier bestpractices.dev answer-sheet skeletons
playbook/{passing,silver,gold}.md   ordered steps with GATE blocks
scripts/                     render.py, preflight.py, gh_settings.py, spdx_headers.py
docs/faq-traps.md            the detection traps (URL literal match, atheris wheels, …)
docs/examples/x402/          the real x402 artifacts, as an attributed worked example
```

## How it works, briefly

1. `render.py` fills templates from a per-repo `hardening.toml`; it **fails hard**
   on any unresolved token and refuses to complete a phase while `FILL:` judgment
   markers survive.
2. `preflight.py` reports MET / UNMET / NEEDS-HUMAN-EVIDENCE per OpenSSF criterion —
   run before (gap analysis) and after (acceptance).
3. `gh_settings.py` applies GitHub-side settings under a **hybrid** safety model:
   dry-run by default, `--apply` for low-risk, `--apply --yes` for the irreversible
   ones.
4. `spdx_headers.py` adds/verifies per-file SPDX + copyright headers (gold).

This repository hardens itself with its own templates.

## Roadmap (next 12 months)

Honest, near-term work only:

- **Now / in flight** — dogfood this skill to OpenSSF silver on itself, then apply
  it to `presidio-hardened-ikigov-assess` and `presidio-hardened-arch-translucency`.
- **Next** — extend `preflight.py` to cover the full gold criteria set; ship a
  reproducible-build helper and a per-file SPDX rollout for gold targets.
- **Later** (under evaluation) — a non-Python language layer (e.g. Rust, for
  `presidio-hardened-treasury`); plugin/marketplace packaging so the skill installs
  without a manual symlink.

## Governance, Architecture, Security

- [Governance](GOVERNANCE.md) — roles, decision process, project continuity.
- [Architecture](ARCHITECTURE.md) — components, trust boundaries, the processing path.
- [Assurance case](ASSURANCE.md) — the security claims and the evidence for each.
- [Security policy](SECURITY.md) — supported versions and how to report a vulnerability.

## License

MIT © PRESIDIO Group. See [LICENSE](LICENSE).
