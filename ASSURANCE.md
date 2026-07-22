# Security Assurance Case

This document is the assurance case for `presidio-hardened-repo`: an explicit argument
for why the project's security requirements are met. It has four parts, as
required by the OpenSSF Best Practices silver criterion `assurance_case`:

1. the threat model,
2. the trust boundaries,
3. the argument that secure design principles are applied, and
4. the argument that common implementation weaknesses are countered.

It is a summary that links to the authoritative detail in
[`SECURITY.md`](SECURITY.md) (controls, per-version threat tables, reporting) and
[`ARCHITECTURE.md`](ARCHITECTURE.md) (components, flow, boundaries) for
`presidio-v/presidio-hardened-repo`.

## 1. Threat model

**Assets.** Two things this tool touches are high-value: (a) the *integrity of a
GitHub repository and its settings* — the tool can write files into a working tree
and, when authorised, change branch protection or visibility; and (b) the
*honesty of a badge attestation* — the answer sheets and criterion statuses the
tool helps produce are claims a third party relies on. On audit-grade,
patent-tied repos a false "Met" is a worse outcome than an honest "Unmet".

| Threat | Control |
|---|---|
| A malicious or malformed manifest/template causes an unintended file write or leaks an unresolved placeholder into an emitted governance doc. | `render.py` fails hard (`RenderError`) on any unresolved or undefined token; its `check` pass reports leftover tokens; a render round-trip and an anti-leak test in `tests/` guard the template tree. |
| The tool makes an **irreversible** GitHub change (make-public exposing history, a branch-protection `enforce_admins` lockout, granting write access) unintentionally. | `gh_settings.py` is dry-run by default; HIGH-risk actions require `--apply` **and** `--yes` (or a typed repo-name confirmation); `make-public` refuses without `--yes` and always prints a "scan history for secrets first" warning. Each step prints a rollback command. |
| The tool **over-claims** a criterion — asserts a false MET the evidence does not support. | `preflight.py` treats a file with an open FILL marker as UNMET, degrades any check it cannot run to NEEDS-HUMAN-EVIDENCE (never a false MET), and the no-over-claim rule in `SKILL.md` binds the judgment work. |
| A skill run clobbers a human-edited target file. | Emission works on a branch → PR; a pre-existing file that diverges from the last emission is surfaced as a diff and merged by hand, not overwritten (playbook idempotency rule). |
| A weakened workflow token or supply-chain change silently loosens a control. | Emitted workflows ship least-privilege `permissions: contents: read`; CodeQL, bandit (ruff `S`), and OpenSSF Scorecard run on every push/PR; release tags are signed. |

**Out of scope (documented, not assumed).** Custody of the `presidio-v` release
signing key is delegated to `git`/`ssh` and the org password manager, not this
tool. The correctness and availability of the `gh` CLI and the GitHub API are the
platform's responsibility; the tool only degrades safely when they are absent.
Whether the human transcribes an honest answer sheet accurately at
bestpractices.dev is a human gate, not a control the tool enforces.

## 2. Trust boundaries

The boundaries below match [ARCHITECTURE.md](ARCHITECTURE.md#trust-boundaries).

- **manifest + templates → `render.py`** — input-validation boundary. Manifest
  and template files are untrusted input; the renderer fails hard on unresolved
  or undefined tokens and the `check` pass blocks open FILL markers, so nothing
  half-rendered crosses into a target repo.
- **`render.py` / `spdx_headers.py` → target working tree** — egress boundary.
  Writes are confined to an explicit `--out` root; divergent pre-existing files
  are surfaced in the PR diff rather than overwritten.
- **`gh_settings.py` → `gh` CLI / GitHub API** — egress (mutation) boundary. All
  mutations complete their dry-run/consequence/rollback presentation before
  crossing; irreversible ones need `--apply --yes`. The tool carries no GitHub
  credential — it uses the operator's existing `gh` authentication.
- **scripts → local git / signing** — egress boundary. Signing is delegated to
  `git`/`ssh` with the org key in `allowed_signers`; the tool holds no key
  material and performs no cryptography of its own.

## 3. Secure design principles applied

**Fail-safe defaults / secure by default.** The two actions that can do harm both
default to the safe outcome. `render.py` fails hard rather than emit an
unresolved token, and its `check` refuses to pass open FILL markers.
`gh_settings.py` is dry-run by default and changes nothing until `--apply`, with
irreversible actions gated behind an additional `--yes`. New controls are opt-in;
an existing default is never weakened silently.

**Complete mediation.** Every emitted file passes through `render.check` (no
tokens, no FILL markers) before a phase is allowed to complete, and `preflight.py`
re-checks each criterion at acceptance. There is no path by which a file reaches
a target repo without going through the strict renderer, and a file with
outstanding judgment work is counted UNMET, not waved through.

**Least privilege.** The tool holds no long-lived secret. It stores no GitHub
token — it borrows the operator's already-authenticated `gh` session — and it
holds no signing key, delegating tag signing to `git`/`ssh` and the shared org
key. The workflows it emits ship `permissions: contents: read`, granting each job
only what it needs.

**Defense in depth.** The controls are independent and layered: strict rendering
plus a CI anti-leak/round-trip test on the templates, preflight's per-criterion
verification, the human gates in the playbook, and continuous analysis (CodeQL,
bandit via ruff `S`, Scorecard). A gap in any one is caught by another.

**Economy of mechanism.** The scripts are stdlib-only Python — no jinja, no
template engine, no dependency graph dragged into the repos being hardened, and no
bespoke cryptography. The one cryptographic operation the release flow relies on —
SSH signing of release tags — is delegated to vetted standard tools (`git`,
`ssh`) with the shared org key. Being pure
Python, the code is memory-safe; there is no manual memory management to get
wrong.

## 4. Common implementation weaknesses countered

| Weakness class | How it is countered |
|---|---|
| **Improper input validation / injection (CWE-20, CWE-74)** | The only untrusted inputs are the tool's own TOML manifest and template files. `render.py` fails hard on undefined/unresolved tokens. Subprocess calls to `git`/`gh` are built as argument lists (never a shell string) and quoted with `shlex` for display only; there is no `shell=True`. bandit (ruff `S`) checks subprocess use continuously. |
| **Memory safety (CWE-119 family)** | N/A in the classic sense — pure Python, memory-safe; no manual allocation, no unsafe FFI. |
| **Cryptographic misuse (CWE-327, CWE-916)** | N/A — the tool implements no cryptography. Release-tag signing is delegated to `git`/`ssh` with the vetted org key. There is no bespoke crypto to misuse. |
| **Hard-coded / exposed secrets (CWE-798, CWE-532)** | The tool stores no secret: no GitHub token (it uses the operator's `gh` session), no signing key (delegated). Scorecard's Token-Permissions and secret-scanning, plus the anti-leak template test, guard against secret material entering the repo. |
| **Insecure network / SSRF (CWE-319, CWE-295)** | N/A — the tool opens no network connections itself. All remote calls go through `gh`, which enforces TLS to the GitHub API. There is no user-supplied URL fetch. |
| **Unsafe deserialization (CWE-502)** | Only trusted, first-party TOML (`tomllib`) and the tool's own JSON from `gh`/coverage are parsed; no untrusted pickle/YAML/eval. |
| **Vulnerable dependencies (CWE-1104)** | The runtime dependency set is the standard library only; dev tooling (ruff, pytest) is monitored by Dependabot and the emitted Scorecard/dependency workflows. |

These classes are checked continuously by **CodeQL**, **bandit** (ruff `S`
rules), and **OpenSSF Scorecard** on every push and pull request. Where a class
does not apply it is marked N/A above with the one-line reason rather than
silently omitted.

## Conclusion

The threats above are each matched to a control; the controls sit at explicit
trust boundaries; the design follows fail-safe, least-privilege, complete-
mediation, defense-in-depth, and economy-of-mechanism principles; and the common
implementation weakness classes are countered by design and checked by automated
analysis. The project's stated security requirements are therefore met, subject
to the documented out-of-scope assumptions.
