# Stability & semver guarantees — presidio-hardened-repo

For downstream integrators depending on this project.

This project is a Claude Code skill, not an importable library. Its public API is
the set of contracts an integrator or a downstream repo depends on:

- **The four script CLIs** and their documented subcommands/flags:
  - `render.py render --manifest --templates --out` and `render.py check <path>`;
  - `preflight.py --repo-path --tier [--manifest] [--strict]`;
  - `gh_settings.py {status,labels,security-features,add-reviewer,branch-protection,make-public} --repo [--apply] [--yes]`;
  - `spdx_headers.py {--check|--apply} [--manifest] <paths>`.
- **The `hardening.toml` manifest schema** — the sections, keys, and enums defined
  in `manifest.schema.json`.
- **The double-brace token contract** — tokens are the manifest flattened as
  `SECTION_KEY` (uppercased), plus the computed `YEAR` and `REPO_SLUG` tokens.
- **The `FILL:` marker convention** (HTML-comment or `#`-comment form) recognised
  by `render.py check` and `preflight.py`.

Internal helper functions, private names (underscore-prefixed), and the exact
template file contents are not part of the public API and may change within a
minor line. There are no grandfathered names.

## Versioning rules (semver, pre-1.0 profile)

- **Patch (0.x.Y):** bug fixes, security fixes, dependency floor bumps. No API
  change, no behaviour change except the fixed defect. Safe to auto-upgrade; this
  is the channel security releases ship on.
- **Minor (0.X.0):** additive API (new exports, new optional parameters with
  defaults, new optional extras). Existing code keeps working, including the
  documented public behaviour. Deprecations are announced here (docstring +
  CHANGELOG) at least one minor before any change.
- **Major (1.0.0+):** the only place deprecated surface may be removed.

**Pin guidance for integrators:** the skill is installed from a clone, not a
package index, so "pinning" means checking out a released `vX.Y.*` tag (rather
than tracking `main`) and running the verification step (below) on every upgrade.

## Behavioural guarantees (stronger than API stability)

These are security invariants, not just interfaces; weakening any of them is
treated as a breaking change regardless of which version component moves.

- **Strict rendering never emits an unresolved token.** `render.py` raises rather
  than write a file containing an unresolved or undefined placeholder. Relaxing
  this to silent substitution is a breaking change.
- **FILL markers gate completion.** A file with an open `FILL:` marker is reported
  by `render.py check` and counted UNMET by `preflight.py`; it is never silently
  treated as done.
- **GitHub mutations are dry-run by default.** `gh_settings.py` changes nothing
  without `--apply`, and irreversible actions additionally require `--yes` (or a
  typed confirmation). Making any mutation execute with fewer signals is breaking.
- **preflight never reports a false MET.** A check that cannot run degrades to
  NEEDS-HUMAN-EVIDENCE, not MET.

## Verifying an installation

Install by symlinking the repo into your Claude Code skills directory, then
confirm the toolchain works:

```bash
scripts/install-skill.sh          # symlinks this repo into ~/.claude/skills/
.venv/bin/python -m pytest tests/ -q     # exit code 0 = the scripts behave as specified
.venv/bin/python scripts/render.py check ARCHITECTURE.md   # "clean: ..." = no open markers
```

After `install-skill.sh`, restart Claude Code (or open a new session) and the
skill appears; ask Claude to "harden this repo to OpenSSF silver" to invoke it. A
passing install is: the pytest suite exits 0 and `render.py check` reports
`clean` on the rendered docs.

## Schema/wire stability

The versioned contract is `manifest.schema.json`, the JSON Schema for
`hardening.toml`. Compatibility rules within a `0.x` line:

- **Adding a new token** (a new optional manifest key, or a new computed token) is
  **backward-compatible** — existing manifests and templates keep working.
- **Removing or renaming a token**, or changing a required field or an enum value,
  is a **breaking change** — existing manifests would stop rendering.
- Templates may add a reference to an already-defined token additively; they may
  not start requiring a token the schema does not define (the renderer would fail
  hard, by design).

The tool also consumes `coverage.json` (`totals.percent_covered` and branch
fields) and GitHub API JSON via `gh`; these are external formats it reads
defensively — a missing or unreadable field degrades to NEEDS-HUMAN-EVIDENCE, not
a crash or a false MET.

## Security response

See [SECURITY.md](SECURITY.md). Security fixes ship as patch releases on the
latest minor; any minimum-safe dependency floors are bumped in the same release.
