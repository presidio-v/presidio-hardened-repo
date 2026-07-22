# Architecture

This document describes the high-level design of `presidio-hardened-repo`: its
components, how data flows through them, and the trust boundaries the project is
built to enforce. For the security requirements and threat model that motivate
this design, see [SECURITY.md](SECURITY.md) and the assurance case in
[ASSURANCE.md](ASSURANCE.md).

## Overview

`presidio-hardened-repo` is a Claude Code skill: an orchestrator document
(`SKILL.md`), a set of stdlib-only Python command-line scripts under `scripts/`,
and a tree of file templates under `templates/`. It hardens *other* GitHub
repositories to a high OpenSSF Scorecard score and the OpenSSF Best Practices
badge by rendering parameterized governance and CI files, checking each OpenSSF
criterion, and applying the GitHub-side settings a badge requires. It is a
developer tool run from a workstation, not a service: it has no network listener,
no daemon, and no persistent state of its own. Its only durable inputs are a
per-target `hardening.toml` manifest, the template files, and CLI arguments; its
outputs are files written into a target repo's working tree and, when explicitly
authorised, mutations to that repo's GitHub settings made by shelling out to the
`gh` CLI. The overriding design stance is *never over-claim*: the scripts verify
and coach but never fabricate a criterion status, and they fail safe (fail-hard
rendering, dry-run mutations) rather than proceed on incomplete input.

## Components

Four scripts, each a single-responsibility command-line tool, plus two template
layers and the manifest that parameterizes them.

| Component | Responsibility |
|---|---|
| `scripts/render.py` | Strict template renderer. Flattens `hardening.toml` into double-brace placeholder values, substitutes them across a template tree, and **fails hard** on any unresolved or undefined token. Its `check` subcommand reports surviving placeholders and open `FILL:` judgment markers so a phase is not declared complete while either remains. It never fills a marker. |
| `scripts/preflight.py` | Gap-analysis and acceptance checker. Reads the manifest and reports each OpenSSF criterion as MET / UNMET / NEEDS-HUMAN-EVIDENCE from filesystem checks, coverage data, and read-only `gh` API queries. A report by default (always exits 0); `--strict` makes UNMET fail. It reuses `render.load_manifest` and `render.find_fill_markers` so its token and FILL contracts are identical to the renderer's. |
| `scripts/gh_settings.py` | GitHub-side settings applier. Drives `gh` to set branch protection, labels, security features, the review collaborator, and visibility. Dry-run by default; low-risk actions need `--apply`, irreversible ones also need `--yes`. |
| `scripts/spdx_headers.py` | Per-file SPDX + copyright header check/insert (gold criterion). `--check` is the CI guard; `--apply` inserts a header after any shebang. Idempotent. |
| `templates/core/` | Language-agnostic governance, Scorecard/CODEOWNERS, and doc skeletons. |
| `templates/python/` | Python-specific CI overlay (ruff, pytest + coverage floors, CodeQL, publish, atheris). Overlays `core` by relative path, so a python file supersedes a same-named core file. |
| `hardening.toml` + `manifest.schema.json` | The per-target parameter source and its versioned schema. |

The scripts share one dependency edge: `preflight.py` and `spdx_headers.py`
import `render.load_manifest`, so the manifest-flattening and FILL-detection logic
is defined once in `render.py` and reused outward.

## Data / processing flow

A hardening run for a target repo is a pipeline:

1. **Manifest → tokens.** `render.py` loads the target's `hardening.toml` and
   flattens it into an uppercase `SECTION_KEY` token map, adding computed
   `YEAR` and `REPO_SLUG` tokens.
2. **Render → files.** It walks `templates/core` (and `templates/python` for a
   `language = "python"` target) and writes each rendered file into the target
   working tree, stripping a single `.tmpl` suffix. Any placeholder the manifest
   cannot resolve raises `RenderError` and aborts the file — a half-rendered
   governance doc never reaches the target.
3. **Judgment → check.** Rendered Class-B docs carry `FILL:` judgment markers
   (HTML comments) where Claude must write honest prose after reading the target
   code.
   `render.py check` reports open markers; the phase is complete only when it is
   clean.
4. **Verify criteria.** `preflight.py` reports MET/UNMET/NEEDS-HUMAN-EVIDENCE. A
   file that exists but still carries a FILL marker is UNMET, not MET.
5. **GitHub settings.** `gh_settings.py` applies the server-side settings, one
   gated step at a time.
6. **Re-verify.** `preflight.py` runs again as acceptance.

The **failure posture is fail-safe**. Rendering fails hard rather than emit an
unresolved token. FILL markers block phase completion rather than let unwritten
judgment pass as done. Every GitHub mutation is dry-run until explicitly applied,
and irreversible ones need a second signal. Remote checks that cannot run (no
`gh`, no admin token) report NEEDS-HUMAN-EVIDENCE, never a false MET. The
load-bearing ordering that is part of the contract: **render must be clean of
tokens and FILL markers before a phase completes**, and **preflight is the
acceptance gate run last**, not a substitute for the human gates in the playbook.

## Trust boundaries

The tool takes input from files it does not fully control and it writes to two
places that matter — a working tree and a GitHub repo. The boundaries below are
referenced by [ASSURANCE.md](ASSURANCE.md#2-trust-boundaries); keep the names
stable.

| Boundary (X → Y) | Kind | Control |
|---|---|---|
| **manifest + templates → `render.py`** | input-validation | The manifest and template files are treated as untrusted input. The renderer fails hard on any unresolved or undefined placeholder, and its `check` pass refuses to let open judgment markers through, so neither an unfilled placeholder nor a token leak can pass into a rendered file silently. |
| **`render.py` / `spdx_headers.py` → target working tree** | egress | Files are written under an explicit `--out` root. Pre-existing target files that diverge from the last emission are surfaced as a PR diff and merged by hand rather than clobbered (playbook idempotency rule). |
| **`gh_settings.py` → `gh` CLI / GitHub API** | egress (mutation) | Every mutation is dry-run by default; low-risk actions need `--apply`, irreversible ones (`make-public`, `add-reviewer`, `branch-protection`) also need `--yes` or a typed confirmation. Each step prints its consequence and a rollback command. The tool holds no GitHub credential of its own — it borrows the operator's authenticated `gh` session. |
| **scripts → local git repo / signing** | egress | The tool never signs or commits on its own. Release tags are SSH-signed by `git` using the shared `presidio-v` org key published in `allowed_signers`; the tool delegates all crypto to `git`/`ssh` and holds no key material. |
