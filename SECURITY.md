# Security Policy

## Supported Versions

Security fixes are provided for the versions listed below. Older lines receive
critical fixes only; unlisted lines are end-of-life.

This project is pre-1.0 and is installed as a Claude Code skill by symlinking the
repository into `~/.claude/skills/` (see `scripts/install-skill.sh`); it is not
distributed as a released PyPI package. Only the latest `0.x` line — the current
`main` — is supported. Upgrade by pulling `main`.

| Version | Supported |
|---------|-----------|
| latest `0.x` (`main`) | ✓ |
| earlier `0.x` | end-of-life — update to the latest `0.x` |

## Reporting a Vulnerability

Please report security vulnerabilities **privately**. Do not open a public issue
for a suspected vulnerability.

- Preferred: open a private GitHub Security Advisory on
  [`presidio-v/presidio-hardened-repo`](https://github.com/presidio-v/presidio-hardened-repo/security/advisories/new)
  (repository **Security** tab → **Report a vulnerability**).
- Alternatively, email security@presidio-group.eu.

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Response process.** You will receive an acknowledgement within **5 business
days**. We aim to release a patch within **30 days** of a confirmed
vulnerability, and will keep you updated on progress until the issue is resolved
or dismissed with a rationale.

**Credit.** We credit reporters of valid vulnerabilities by name in the
published GitHub Security Advisory and in the `CHANGELOG.md` entry for the fix,
unless the reporter asks to remain anonymous.

## Threat Model and Security Controls

> Skeleton — complete from the target codebase. Do not copy controls from another
> project, and do not claim a control the code does not implement.

### Security controls

| Control | Mode / how to enable |
|---|---|
| **Fail-hard rendering** — `render.py` raises on any unresolved or undefined placeholder rather than emit a partial file. | Automatic; every render. |
| **FILL-marker gate** — `render.py check` reports open `FILL:` judgment markers, and `preflight.py` counts a file that still has one as UNMET. | Automatic; run `check` before completing a phase. |
| **Dry-run-by-default GitHub mutations** — `gh_settings.py` prints command + consequence + rollback and changes nothing without `--apply`. | Default. `--apply` for low-risk; `--apply --yes` (or typed confirmation) for irreversible actions; `make-public` refuses without `--yes`. |
| **No stored credentials or keys** — the tool holds no GitHub token and no signing key; it borrows the operator's `gh` session and delegates tag signing to `git`/`ssh`. | Automatic; structural. |
| **CI anti-leak / render round-trip tests** — `tests/` verify the template tree renders cleanly and contains no leaked example-domain content or tokens. | Automatic in CI on every push/PR. |
| **Least-privilege workflow tokens** — emitted GitHub Actions ship `permissions: contents: read`. | Applied to rendered workflows. |
| **Continuous static analysis** — CodeQL, bandit (ruff `S` rules), and OpenSSF Scorecard. | Automatic in CI. |
| **SSH-signed release tags** — release tags are signed with the `presidio-v` org key published in `allowed_signers`. | Applied at release; verify with `git verify-tag` or the GitHub API. |
| **Per-file SPDX headers** — `spdx_headers.py --check` guards headers in CI (gold). | Opt-in CI guard; `--apply` inserts them. |

### Threat model

The tool protects two assets: the **integrity of the target repository** (files
and GitHub settings it can change) and the **honesty of the badge attestations**
it helps produce. Its trust boundaries are the untrusted manifest/templates it
reads, the target working tree it writes, the `gh`/GitHub API it mutates, and the
local git repo it signs through.

| Threat | Mitigation |
|---|---|
| Malformed manifest/template leaks a token or emits a partial file | `render.py` fails hard; `check` and CI tests catch leftovers |
| Unintended irreversible GitHub change (make-public, lockout, write grant) | `gh_settings.py` dry-run default; `--yes` gate; rollback printed per step |
| Over-claiming a criterion status | FILL-as-UNMET; degrade-to-NEEDS-HUMAN-EVIDENCE; no-over-claim rule in `SKILL.md` |
| Clobbering a human-edited target file | branch → PR emission; divergence surfaced as a diff, not overwritten |

For the full assurance case — threat model, trust boundaries, secure-design
argument, and how common implementation weaknesses are countered — see
[`ASSURANCE.md`](ASSURANCE.md).

For the consolidated assurance case — threat model, trust boundaries,
secure-design argument, and how common implementation weaknesses are countered —
see [`ASSURANCE.md`](ASSURANCE.md).

## Verifying Releases and Obtaining Public Signing Keys

Release artefacts and git tags are signed. There is no key to fetch by hand for
artefact verification; the trusted identities are described below.

- **Release artefacts** are verified with Sigstore-backed build provenance. The
  trusted identity is the repository's OIDC signer — run:

  ```bash
  gh attestation verify <artefact> --repo presidio-v/presidio-hardened-repo
  ```

- **Git release tags** are SSH-signed with the organisation's release signing
  key, which is registered as a **signing key** on the maintainer's GitHub
  account, so each release tag shows as **Verified** on the Releases page and via
  the API:

  ```bash
  gh api repos/presidio-v/presidio-hardened-repo/git/tags/<sha> --jq .verification.verified
  ```

  The public key is published in the repository's
  [`allowed_signers`](allowed_signers) file. To verify a tag locally:

  ```bash
  git -c gpg.ssh.allowedSignersFile=allowed_signers verify-tag <tag>
  ```

- **Package-registry releases** carry PEP 740 (or the registry's equivalent)
  attestations published via Trusted Publishing (OIDC, no stored API tokens);
  standard tooling and the registry UI surface these automatically.
