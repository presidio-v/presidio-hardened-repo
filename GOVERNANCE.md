# Project Governance

`presidio-hardened-repo` is developed and maintained by **PRESIDIO Group**
and published under the `presidio-v` GitHub organisation. This document
describes how the project is governed, who holds which responsibilities, and how
the project continues to function if any single individual becomes unavailable.

## Governance model

The project follows a **maintainer-led, single-steward** model.
PRESIDIO Group is the steward organisation: it owns the repository and the
release signing key, and it sets the security bar the project is held to.

Day-to-day technical decisions are made by the maintainers by rough consensus:

- **Ordinary changes** (bug fixes, tests, documentation, dependency floors) are
  decided by the reviewing maintainer on the pull request.
- **Security-relevant changes** (anything touching the project's
  security-sensitive modules, listed below) require an explicit security
  rationale in the pull request and must not weaken an existing default. See
  [CONTRIBUTING.md](CONTRIBUTING.md#security-sensitive-changes). For this project
  those areas are: `scripts/gh_settings.py` (it mutates GitHub repo/org settings,
  including irreversible ones); the file-writing paths in `scripts/render.py` and
  `scripts/spdx_headers.py` (they write into target repositories); the
  no-over-claim rule and the FILL-marker / token strictness that enforce honest
  attestations; and the answer-sheet skeletons under `templates/sheets/`, which
  render into badge attestations a third party relies on.
- **Public-API and compatibility changes** are governed by [SEMVER.md](SEMVER.md);
  a breaking change requires a major/minor bump per the documented policy.
- **Disagreements** that cannot be resolved on the pull request are escalated to
  the steward organisation (PRESIDIO Group), whose decision is final.

There is no pay-to-play influence: contribution weight is earned through review
history and sustained, high-quality contribution, not funding.

## Roles and responsibilities

| Role | Held by | Responsibilities |
|---|---|---|
| **Steward organisation** | PRESIDIO Group (`presidio-v` GitHub org) | Owns the repository and release infrastructure; holds and can recover all release credentials; final escalation authority; ensures continuity (see below). |
| **Maintainer** | PRESIDIO Group engineering | Reviews and merges pull requests; enforces the test, style, and security bars; cuts releases; triages issues; is the point of accountability for the codebase. |
| **Security contact** | PRESIDIO Group security | Receives and triages private vulnerability reports (see [SECURITY.md](SECURITY.md)); coordinates fixes, advisories, and reporter credit. Reachable at `security@presidio-group.eu` and via GitHub Security Advisories. |
| **Release manager** | PRESIDIO Group engineering | Owns the SSH-signed-tag release flow; verifies that each release tag is signed and shows as **Verified** on GitHub. |
| **Contributor** | Anyone | Opens issues and pull requests under [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). |

Roles are held by function within PRESIDIO Group rather than being
tied to one named individual, so responsibilities transfer without a change to
this document.

## Becoming a maintainer

A contributor with a sustained track record of merged, high-quality changes —
particularly to the security-sensitive modules — may be invited by the steward
organisation to become a maintainer. Maintainership is granted by
PRESIDIO Group and recorded by adding the person to the
`presidio-v` organisation with the appropriate repository role.

## Project continuity

The project is structured so that it continues to function — issues can be
triaged and closed, contributions can be reviewed and accepted, and new versions
can be released — within one week even if any single individual becomes
unavailable. This is a property of the **organisation**, not of any one person:

- **Repository ownership** is held by the `presidio-v` GitHub organisation,
  not by a personal account. Organisation owners can grant repository and release
  access to another member at any time.
- **Release credentials are not personal.** The project is not published to a
  package index; a release is an SSH-signed git tag on the org-owned repository,
  so there is no personal publish token that dies with an individual. The release
  signing key is the shared `presidio-v` org key: its public half is in
  [`allowed_signers`](allowed_signers) and its private half is held in the
  organisation's password manager (custody ultimately with PRESIDIO Group's
  leadership), not solely on any one contributor's machine, so it is recoverable.
- **The release process is fully documented** — see the SSH-signed-tag flow in
  [SECURITY.md](SECURITY.md#verifying-releases-and-obtaining-public-signing-keys)
  — so any authorised PRESIDIO Group engineer can cut a release by following it.
- **PRESIDIO Group is a staffed organisation** with more than one
  person able to assume the maintainer, security-contact, and release-manager
  roles above.

The project's bus factor is therefore backed by the steward organisation rather
than a lone maintainer.
