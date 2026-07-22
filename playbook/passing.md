# Playbook — OpenSSF **passing** (Scorecard CII check → 5)

Goal: the OpenSSF Best Practices *passing* badge and a solid Scorecard baseline.
Work on a branch → PR; never commit to `main` directly. Steps are idempotent.

## 0. Preflight
```
python scripts/preflight.py --repo-path <repo> --tier passing
```
Read the output. Read enough of the target codebase to fill the judgment work
honestly later (what it does, its trust boundaries, its crypto use, its inputs).

## 1. Manifest
Copy `hardening.toml` to `<repo>/hardening.toml` and edit `[project]`, `[people]`,
`[legal]`. Set `[project].tier = "passing"`. Validate against `manifest.schema.json`.

## 2. Emit baseline files (branch)
```
python scripts/render.py render --manifest <repo>/hardening.toml --templates templates/core   --out <repo>
# python target:
python scripts/render.py render --manifest <repo>/hardening.toml --templates templates/python --out <repo>
python scripts/render.py check <repo>          # must reach: no unresolved tokens
```
Passing needs at least: `LICENSE`, `README` (description + how to obtain/report),
`SECURITY.md` (reporting process), `CONTRIBUTING.md` (contribution + tests policy),
`CHANGELOG.md`, CI (`ci.yml`), `codeql.yml`, `scorecard.yml`, `dependabot.yml`.
Splice `README-fragments.md` into the existing README (badges + links).

## 3. Judgment work (you, Claude — from the target code)
Resolve every FILL marker `render.py check` reports. For passing this is mainly:
- `SECURITY.md` threat-model / controls skeleton (`FILL:threat-model`, `FILL:security-controls`)
- `CONTRIBUTING.md` `FILL:security-sensitive-modules`
- answer-sheet justifications (step 6)
Do not invent facts. If the code has no crypto, say so; if there is no fuzz target
yet, add one (step 5) rather than claiming dynamic analysis you don't run.

## 4. Tests, lint, coverage (python)
Ensure `ci.yml` runs ruff + `ruff format --check` and the pytest matrix with
`--cov=<package> --cov-fail-under=90 --cov-branch`. Get the suite green. Passing
only needs "most" coverage, but the CI gate we ship is the gold floor — set it
now so silver/gold need no CI change.

## 5. Fuzz harness (python — for `dynamic_analysis` and the Scorecard Fuzzing check)
Render `templates/python/fuzz/`. Point `FILL:fuzz-target` at a real
canonicalisation/parse/digest function. The harness MUST keep the literal line
`import atheris`. Add the Atheris fuzz job to `ci.yml` (Linux, Python 3.12).

## 6. Answer sheet
```
python scripts/render.py render --manifest <repo>/hardening.toml   --templates templates/sheets --out <repo>/plan
```
Fill `plan/cii-passing-answers.md` FILL markers honestly from the evidence above.
Then turn the filled sheet into a click-to-propose URL for the human (faster than
hand-entering each criterion at bestpractices.dev; the human still reviews and
accepts every highlighted proposal — unforced, existing answers are not touched
unless `--overrides` is passed):
```
python scripts/answersheet_to_proposal.py --sheet <repo>/plan/cii-passing-answers.md --repo-path <repo>
```
(Needs `[badge].bestpractices_id` set in the manifest, or pass `--id N`. A long
sheet is split into several URLs — open each.)

## 7. GATES (one at a time — stop for a human "go")

> ### GATE P1 — make the repo public (only if currently private)
> Passing requires `repo_public`. **Irreversible disclosure.**
> First: scan history for secrets (`git log` review; `gh` secret scanning).
> ```
> python scripts/gh_settings.py make-public --repo <org>/<repo>            # dry-run
> python scripts/gh_settings.py make-public --repo <org>/<repo> --apply --yes
> ```
> Consequence: the full history becomes world-readable, permanently.

> ### GATE P2 — create the Scorecard PAT (manual, GitHub UI)
> Scorecard's Branch-Protection check needs a fine-grained PAT with `admin:read`
> on the repo, stored as the `SCORECARD_TOKEN` secret. Create it in the GitHub UI
> (Settings → Developer settings → fine-grained tokens), add it as a repo secret.
> Without it, Branch-Protection errors but the rest of Scorecard still scores.

> ### GATE P3 — register at bestpractices.dev (manual, human login)
> Log in with GitHub (the `read:org` grant is unused — declining is fine). Create
> the project with the URL **exactly** `https://github.com/<org>/<repo>`. Paste the
> answers from `plan/cii-passing-answers.md`. Record the numeric project id back
> into `hardening.toml` `[badge].bestpractices_id` and re-render the README badge.

## 8. Low-risk config (safe to apply together)
```
python scripts/gh_settings.py labels           --repo <org>/<repo> --apply
python scripts/gh_settings.py security-features --repo <org>/<repo> --apply
```

## 9. Verify
```
python scripts/preflight.py --repo-path <repo> --tier passing
```
Then let the weekly Scorecard action run (or run the `scorecard` CLI locally) and
confirm the CII check moves to 5 once the badge is live.
