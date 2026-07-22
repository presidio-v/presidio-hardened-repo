# Detection traps and gotchas

Hard-won specifics from hardening `presidio-hardened-x402`. Getting any of these
wrong silently costs a check or a badge.

## bestpractices.dev / Scorecard CII

- **Register the project URL as an exact literal** `https://github.com/<org>/<repo>`.
  Scorecard does a literal DB string match against the BadgeApp. A trailing slash,
  a `www.`, or the PyPI URL returns `NotFound` → the CII-Best-Practices check reads
  0 even with a real badge.
- Log in to bestpractices.dev with GitHub. It requests `read:org`, but no code path
  consumes it — declining the org grant is fine.
- The badge **embed URL is identical** for passing/silver/gold; the image
  auto-renders the current level. No README edit is needed on a level-up.
- Silver requires passing first; gold requires silver first.
- Poll status machine-readably: `GET https://www.bestpractices.dev/projects/<id>.json`.
- `answersheet_to_proposal.py` turns a filled answer sheet into an *automation
  proposal* URL (`/projects/<id>/choose/edit?<crit>_status=…`) so the human clicks
  once and reviews/accepts each highlighted proposal instead of hand-entering every
  criterion. It only proposes and is **unforced** by default (fills blank fields
  only; `--overrides '*'` overwrites). A full passing sheet (~67 criteria) exceeds
  the ~6000-char URL cap, so it is split across **several** URLs — open each; no
  criterion is ever dropped.

## Scorecard checks

- **Fuzzing** is detected for Python by the literal string `import atheris`. It does
  **not** detect Hypothesis or property-based libraries. Keep that exact line in the
  fuzz harness or the check reads 0.
- **Branch-Protection** cannot be read by the default `GITHUB_TOKEN`. Store a
  fine-grained PAT with `admin:read` on the repo as the `SCORECARD_TOKEN` secret;
  the workflow falls back to `github.token` when the secret is absent (non-breaking,
  but that check then errors).
- **Code-Review** scores 0 for a single-contributor project — Scorecard credits the
  *merger of another person's PR* as an approver. The external reviewer / two-person
  gate is therefore the single highest-leverage change for both the Scorecard score
  and the silver/gold review criteria.
- **Maintained** is inconclusive for repos younger than ~90 days.
- **SAST** detects CodeQL / SonarCloud; it does not detect Checkmarx/Snyk/Fortify.
- **Pinned-Dependencies** wants GitHub Actions pinned to commit SHAs (not tags) —
  every `uses:` in every workflow. Keep the `# vX.Y.Z` trailing comment for humans.
- **Token-Permissions** wants an explicit least-privilege `permissions:` block
  (ideally `contents: read` at the workflow top, elevated per-job only as needed).

## Atheris (Python fuzzing)

- No macOS wheel — the fuzz job must run on Linux CI only.
- No cp310 wheel for recent Atheris — run the fuzz job under Python 3.12 (the test
  matrix is unaffected; keep 3.10–3.13 there).
- An editable install (`pip install -e`) can let the source tree shadow the
  installed package; make sure the harness imports the module actually under test.

## Signed releases

- Release **tags** are SSH-signed with the shared `presidio-v` org key; commits are
  left unsigned. The public half is in `allowed_signers` for local verification.
- Confirm GitHub-side verification per release:
  `gh api repos/<org>/<repo>/git/tags/<tagsha> --jq .verification.verified` → `true`.

## Coverage

- Gold needs ≥90% statement AND ≥80% branch. Enable `--cov-branch`; the *blended*
  number can sit below the statement number, so gate each metric separately.
- Cheapest coverage to recover is on error paths, optional-import fallbacks, and
  custom exception `__init__`s.
