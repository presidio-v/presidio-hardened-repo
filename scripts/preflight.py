# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Gap-analysis + acceptance checker for a hardened target repository.

``preflight.py`` reads a target repo's ``hardening.toml`` manifest and reports,
per OpenSSF Best Practices criterion for a chosen ``--tier``, one of three
verdicts:

* **MET** — a machine check confirms the criterion is satisfied on disk or via
  the GitHub API.
* **UNMET** — a machine check ran and the criterion is *not* satisfied. This is
  the actionable list: create the file, enable the branch rule, register the
  badge.
* **NEEDS-HUMAN-EVIDENCE** — the criterion is inherently a human attestation
  (secure-design knowledge, reviewer independence) *or* a check could not run
  (``gh`` missing / unauthenticated, no admin token, artefact absent). It is not
  a failure; it is a hand-off to a person.

The tool is a *report*, not a gate: it always exits 0 so it can run in CI for
information without breaking the build. ``--strict`` flips that — any UNMET then
exits non-zero, which is the mode to wire into a release check once a repo is
meant to stay hardened.

Design notes:

* stdlib only, Python 3.11+ (``tomllib`` via the shared ``render`` module).
* Manifest flattening is reused verbatim from ``render.load_manifest`` so the
  token contract is identical to the renderer's; FILL-marker detection is reused
  from ``render.find_fill_markers`` so "file exists but still has open judgment
  work" is treated as UNMET, not MET.
* Every remote check degrades gracefully: if ``gh`` is absent or unauthorised
  the check reports NEEDS-HUMAN-EVIDENCE with the reason, never a false MET.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render  # noqa: E402

MET = "MET"
UNMET = "UNMET"
HUMAN = "NEEDS-HUMAN-EVIDENCE"

GRP_FILES = "Files"
GRP_SOURCE = "Source"
GRP_COVERAGE = "Coverage"
GRP_REGISTRATION = "Registration"
GRP_REMOTE = "Remote (gh)"
GRP_HUMAN = "Human evidence"

# Tier ordering; higher tiers include every lower tier's criteria.
TIER_ORDER = {"passing": 0, "silver": 1, "gold": 2}

# Minimum statement-coverage percentage a tier requires. Branch coverage is
# reported for information only (no passing/silver branch floor is a MUST; gold
# adds a branch floor, checked in CI, not gated here).
TIER_STATEMENT_FLOOR = {"passing": 60.0, "silver": 80.0, "gold": 90.0}

# Coverage criterion name differs by tier.
COVERAGE_CRITERION = {
    "passing": "test_most",
    "silver": "test_statement_coverage80",
    "gold": "test_statement_coverage90",
}

# Some criteria are only assessed at (and above) a given tier. A criterion not
# listed here defaults to "passing" (assessed at every tier). This keeps a
# passing/silver preflight from reporting gold-only criteria (per-file SPDX,
# org-wide 2FA) as UNMET — they belong to the gold tier alone.
CRITERION_MIN_TIER = {
    "per_file_license_spdx": "gold",
    "require_2FA": "gold",
}


class Result(NamedTuple):
    group: str
    criterion: str
    status: str
    reason: str


# Files that must exist AND be free of open FILL markers. Each entry is a tuple
# of (candidate filenames, criterion, minimum tier at which it applies).
FILE_CHECKS: list[tuple[tuple[str, ...], str, str]] = [
    (("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"), "license_location", "passing"),
    (("README.md", "README.rst", "README"), "description_good", "passing"),
    (("SECURITY.md",), "vulnerability_report_process", "passing"),
    (("CONTRIBUTING.md",), "contribution", "passing"),
    (("SEMVER.md",), "version_semver", "passing"),
    (("CHANGELOG.md",), "release_notes", "passing"),
    ((".github/CODEOWNERS", "CODEOWNERS"), "two_person_review", "passing"),
    ((".github/dependabot.yml", ".github/dependabot.yaml"), "dependency_monitoring", "passing"),
    ((".github/workflows/scorecard.yml",), "static_analysis_scorecard", "passing"),
    ((".github/workflows/codeql.yml",), "static_analysis_common_vulnerabilities", "passing"),
    (("CODE_OF_CONDUCT.md",), "code_of_conduct", "silver"),
    (("GOVERNANCE.md",), "governance", "silver"),
    (("ARCHITECTURE.md",), "documentation_architecture", "silver"),
    (("ASSURANCE.md",), "assurance_case", "silver"),
    (("allowed_signers",), "version_tags_signed", "silver"),
]

# Inherently human criteria — no file or API answers them. (criterion, tier, reason)
HUMAN_CRITERIA: list[tuple[str, str, str]] = [
    ("report_responses", "passing", "maintainer responsiveness — verify from issue history"),
    ("know_secure_design", "passing", "secure-design knowledge is a maintainer attestation"),
    ("security_review", "silver", "independent security review — attach the report"),
    ("contributors_unassociated", "silver", "2+ unassociated contributors — human judgement"),
    ("build_reproducible", "silver", "reproducible/hermetic build — human verification"),
]


def _tier_applies(entry_tier: str, target_tier: str) -> bool:
    return TIER_ORDER[entry_tier] <= TIER_ORDER[target_tier]


# ---------------------------------------------------------------------------
# Local (filesystem) checks
# ---------------------------------------------------------------------------
def _first_existing(repo: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = repo / name
        if candidate.is_file():
            return candidate
    return None


def check_files(repo: Path, tier: str) -> list[Result]:
    """Each required doc must exist and carry no surviving FILL markers."""
    results: list[Result] = []
    for names, criterion, entry_tier in FILE_CHECKS:
        if not _tier_applies(entry_tier, tier):
            continue
        found = _first_existing(repo, names)
        if found is None:
            results.append(Result(GRP_FILES, criterion, UNMET, f"missing: {names[0]}"))
            continue
        text = found.read_text(encoding="utf-8", errors="replace")
        fills = render.find_fill_markers(text)
        if fills:
            reason = f"{found.name}: open FILL markers: {', '.join(fills)}"
            results.append(Result(GRP_FILES, criterion, UNMET, reason))
        else:
            results.append(Result(GRP_FILES, criterion, MET, found.name))
    return results


# Whole-word "test"/"tests" so a job name / step matches but "ubuntu-latest" does not.
_TEST_WORD_RE = re.compile(r"\btests?\b")


def check_continuous_integration(repo: Path) -> list[Result]:
    """Any ``.github/workflows/*.yml|*.yaml`` that runs the test suite satisfies CI.

    The criterion is met by *any* workflow whose contents invoke ``pytest`` or
    carry a job/step/name with the whole word "test" — not only a file literally
    named ``ci.yml`` (flagship repos use ``pytest.yml``, ``test.yml``, …). Reports
    which workflow satisfied it.
    """
    crit = "test_continuous_integration"
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.is_dir():
        return [Result(GRP_FILES, crit, UNMET, "no .github/workflows/ directory")]
    workflows = sorted(p for p in wf_dir.iterdir() if p.is_file() and p.suffix in (".yml", ".yaml"))
    if not workflows:
        return [Result(GRP_FILES, crit, UNMET, "no workflow files under .github/workflows/")]
    for wf in workflows:
        try:
            text = wf.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if "pytest" in text or _TEST_WORD_RE.search(text):
            return [Result(GRP_FILES, crit, MET, f"{wf.name} runs the test suite")]
    scanned = ", ".join(w.name for w in workflows)
    return [Result(GRP_FILES, crit, UNMET, f"no test-running workflow (scanned: {scanned})")]


def _has_spdx(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:2048]
    except OSError:
        return False
    return "SPDX-License-Identifier" in head


def check_spdx_headers(repo: Path) -> list[Result]:
    """Sample every ``*.py`` under ``src/`` for an SPDX identifier line."""
    crit = "per_file_license_spdx"
    src = repo / "src"
    if not src.is_dir():
        return [Result(GRP_SOURCE, crit, HUMAN, "no src/ directory (non-python or other layout)")]
    pys = sorted(src.rglob("*.py"))
    if not pys:
        return [Result(GRP_SOURCE, crit, HUMAN, "no .py sources under src/")]
    missing = [p for p in pys if not _has_spdx(p)]
    total = len(pys)
    if not missing:
        return [Result(GRP_SOURCE, crit, MET, f"{total}/{total} src .py files carry SPDX")]
    sample = ", ".join(p.relative_to(repo).as_posix() for p in missing[:3])
    return [Result(GRP_SOURCE, crit, UNMET, f"{len(missing)}/{total} missing SPDX (e.g. {sample})")]


def check_fuzzing(repo: Path) -> list[Result]:
    """Scorecard Fuzzing: a literal ``import atheris`` somewhere under fuzz/."""
    crit = "dynamic_analysis"
    fuzz = repo / "fuzz"
    if not fuzz.is_dir():
        return [Result(GRP_SOURCE, crit, UNMET, "no fuzz/ directory; add an Atheris harness")]
    for path in fuzz.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "import atheris" in text:
            rel = path.relative_to(repo).as_posix()
            return [Result(GRP_SOURCE, crit, MET, f"import atheris in {rel}")]
    return [Result(GRP_SOURCE, crit, UNMET, "fuzz/ present but no 'import atheris' harness")]


def check_coverage(repo: Path, tier: str) -> list[Result]:
    """Read ``coverage.json`` totals and compare statement coverage to the floor."""
    crit = COVERAGE_CRITERION[tier]
    cov = repo / "coverage.json"
    if not cov.is_file():
        note = "no coverage.json; run pytest --cov --cov-report=json"
        return [Result(GRP_COVERAGE, crit, HUMAN, note)]
    try:
        totals = json.loads(cov.read_text(encoding="utf-8")).get("totals", {})
    except (OSError, ValueError):
        return [Result(GRP_COVERAGE, crit, HUMAN, "coverage.json present but unreadable")]

    stmt = totals.get("percent_covered")
    num_branches = totals.get("num_branches") or 0
    covered_branches = totals.get("covered_branches") or 0
    branch_pct = (100.0 * covered_branches / num_branches) if num_branches else None

    if stmt is None:
        return [Result(GRP_COVERAGE, crit, HUMAN, "coverage.json has no totals.percent_covered")]

    floor = TIER_STATEMENT_FLOOR[tier]
    branch_note = f", branch {branch_pct:.1f}%" if branch_pct is not None else ""
    reason = f"statement {stmt:.1f}% (floor {floor:.0f}%){branch_note}"
    status = MET if stmt >= floor else UNMET
    return [Result(GRP_COVERAGE, crit, status, reason)]


def check_registration(tokens: dict[str, str]) -> list[Result]:
    """The badge project id must be set (non-zero) in the manifest."""
    crit = "cii_best_practices_badge"
    raw = tokens.get("BADGE_BESTPRACTICES_ID", "0").strip()
    if raw.isdigit() and int(raw) != 0:
        return [Result(GRP_REGISTRATION, crit, MET, f"bestpractices.dev project {raw}")]
    note = "register at bestpractices.dev, set badge.bestpractices_id in hardening.toml"
    return [Result(GRP_REGISTRATION, crit, UNMET, note)]


# ---------------------------------------------------------------------------
# Remote checks via the gh CLI. Every one degrades to NEEDS-HUMAN-EVIDENCE if
# gh is missing, unauthenticated, or lacks the scope to read the setting.
# ---------------------------------------------------------------------------
def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _gh(args: list[str]) -> tuple[int, str]:
    """Run ``gh <args>``; return (returncode, stdout). 127 if gh is absent."""
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, ""
    return proc.returncode, proc.stdout


def _gh_json(args: list[str]) -> object | None:
    rc, out = _gh(args)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def check_repo_public(slug: str) -> list[Result]:
    crit = "repo_public"
    data = _gh_json(["api", f"repos/{slug}"])
    if not isinstance(data, dict):
        return [Result(GRP_REMOTE, crit, HUMAN, "gh unavailable/unauthenticated or repo not found")]
    visibility = data.get("visibility") or ("private" if data.get("private") else "public")
    if visibility == "public":
        return [Result(GRP_REMOTE, crit, MET, "repository is public")]
    return [Result(GRP_REMOTE, crit, UNMET, f"repository visibility is {visibility}")]


def check_branch_protection(slug: str) -> list[Result]:
    crit = "branch_protection"
    data = _gh_json(["api", f"repos/{slug}/branches/main/protection"])
    if not isinstance(data, dict):
        note = "no admin token or no protection on main (gh could not read it)"
        return [Result(GRP_REMOTE, crit, HUMAN, note)]
    rpr = data.get("required_pull_request_reviews") or {}
    count = rpr.get("required_approving_review_count", 0)
    code_owner = bool(rpr.get("require_code_owner_reviews"))
    admins = bool((data.get("enforce_admins") or {}).get("enabled"))

    failures = []
    if count < 1:
        failures.append("no required approving review")
    if not code_owner:
        failures.append("code-owner review not required")
    if not admins:
        failures.append("admins not included (enforce_admins off)")
    if failures:
        return [Result(GRP_REMOTE, crit, UNMET, "; ".join(failures))]
    reason = f">={count} review, code-owner required, admins enforced"
    return [Result(GRP_REMOTE, crit, MET, reason)]


def check_good_first_issue(slug: str) -> list[Result]:
    crit = "good_first_issue_label"
    data = _gh_json(["api", f"repos/{slug}/labels", "--paginate"])
    if not isinstance(data, list):
        return [Result(GRP_REMOTE, crit, HUMAN, "gh unavailable/unauthenticated")]
    names = {lbl.get("name", "").lower() for lbl in data if isinstance(lbl, dict)}
    if "good first issue" in names:
        return [Result(GRP_REMOTE, crit, MET, "'good first issue' label exists")]
    return [Result(GRP_REMOTE, crit, UNMET, "no 'good first issue' label")]


def check_reviewer_collaborator(slug: str, reviewer: str) -> list[Result]:
    crit = "two_person_review_collaborator"
    if not reviewer:
        return [Result(GRP_REMOTE, crit, HUMAN, "no reviewer set in manifest")]
    rc, _ = _gh(["api", f"repos/{slug}/collaborators/{reviewer}"])
    if rc == 127:
        return [Result(GRP_REMOTE, crit, HUMAN, "gh unavailable")]
    if rc == 0:
        return [Result(GRP_REMOTE, crit, MET, f"{reviewer} is a collaborator")]
    note = f"{reviewer} is not a collaborator (or token lacks scope to see it)"
    return [Result(GRP_REMOTE, crit, UNMET, note)]


def check_tag_verification(slug: str) -> list[Result]:
    crit = "version_tags_signed_verified"
    refs = _gh_json(["api", f"repos/{slug}/git/refs/tags"])
    if not isinstance(refs, list):
        return [Result(GRP_REMOTE, crit, HUMAN, "gh unavailable or no tags")]
    if not refs:
        return [Result(GRP_REMOTE, crit, UNMET, "no tags in the repository")]
    annotated = [
        r for r in refs if isinstance(r, dict) and (r.get("object") or {}).get("type") == "tag"
    ]
    if not annotated:
        note = "only lightweight tags found; releases should be annotated + signed"
        return [Result(GRP_REMOTE, crit, UNMET, note)]
    sha = annotated[-1]["object"]["sha"]
    tag = _gh_json(["api", f"repos/{slug}/git/tags/{sha}"])
    if not isinstance(tag, dict):
        return [Result(GRP_REMOTE, crit, HUMAN, "could not fetch the tag object")]
    verified = bool((tag.get("verification") or {}).get("verified"))
    name = tag.get("tag", sha[:12])
    if verified:
        return [Result(GRP_REMOTE, crit, MET, f"latest signed tag {name} verifies")]
    return [Result(GRP_REMOTE, crit, UNMET, f"tag {name} signature not verified")]


def check_org_2fa(slug: str) -> list[Result]:
    crit = "require_2FA"
    org = slug.split("/", 1)[0]
    data = _gh_json(["api", f"orgs/{org}"])
    if not isinstance(data, dict):
        return [Result(GRP_REMOTE, crit, HUMAN, "gh unavailable, or not an org / not visible")]
    val = data.get("two_factor_requirement_enabled")
    if val is None:
        return [Result(GRP_REMOTE, crit, HUMAN, "2FA requirement is visible only to org admins")]
    if val:
        return [Result(GRP_REMOTE, crit, MET, "org requires two-factor auth")]
    return [Result(GRP_REMOTE, crit, UNMET, "org does not require two-factor auth")]


def check_remote(slug: str, reviewer: str) -> list[Result]:
    """All gh-backed checks; short-circuit to HUMAN when gh is absent."""
    if not _gh_available():
        note = "gh CLI not installed; install and authenticate to check remote settings"
        criteria = [
            "repo_public",
            "branch_protection",
            "good_first_issue_label",
            "two_person_review_collaborator",
            "version_tags_signed_verified",
            "require_2FA",
        ]
        return [Result(GRP_REMOTE, c, HUMAN, note) for c in criteria]

    results: list[Result] = []
    results += check_repo_public(slug)
    results += check_branch_protection(slug)
    results += check_good_first_issue(slug)
    results += check_reviewer_collaborator(slug, reviewer)
    results += check_tag_verification(slug)
    results += check_org_2fa(slug)
    return results


def human_criteria(tier: str) -> list[Result]:
    return [
        Result(GRP_HUMAN, criterion, HUMAN, reason)
        for criterion, entry_tier, reason in HUMAN_CRITERIA
        if _tier_applies(entry_tier, tier)
    ]


# ---------------------------------------------------------------------------
# Orchestration + reporting
# ---------------------------------------------------------------------------
def run_checks(repo: Path, tier: str, tokens: dict[str, str], slug: str) -> list[Result]:
    reviewer = tokens.get("PEOPLE_REVIEWER", "")
    results: list[Result] = []
    results += check_files(repo, tier)
    results += check_continuous_integration(repo)
    results += check_spdx_headers(repo)
    results += check_fuzzing(repo)
    results += check_coverage(repo, tier)
    results += check_registration(tokens)
    results += check_remote(slug, reviewer)
    results += human_criteria(tier)
    # Drop criteria that belong only to a higher tier than the one requested
    # (e.g. per-file SPDX and org 2FA are gold-only; do not report them UNMET at
    # passing/silver). Criteria absent from the map default to "passing".
    return [
        r for r in results if _tier_applies(CRITERION_MIN_TIER.get(r.criterion, "passing"), tier)
    ]


def print_report(results: list[Result], tier: str, slug: str) -> Counter[str]:
    print(f"preflight — {slug} — tier: {tier}\n")
    groups: dict[str, list[Result]] = {}
    for r in results:
        groups.setdefault(r.group, []).append(r)

    for group, rows in groups.items():
        print(f"{group}")
        for r in rows:
            print(f"  {r.status:<22} {r.criterion:<34} {r.reason}")
        print()

    counts: Counter[str] = Counter(r.status for r in results)
    print(
        f"summary: {counts[MET]} MET  |  {counts[UNMET]} UNMET  |  "
        f"{counts[HUMAN]} NEEDS-HUMAN-EVIDENCE  ({len(results)} criteria checked)"
    )
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gap-analysis + acceptance checker for a hardened repo.",
    )
    parser.add_argument("--repo-path", required=True, help="path to the target repo working tree")
    parser.add_argument(
        "--tier", required=True, choices=sorted(TIER_ORDER), help="target OpenSSF tier"
    )
    parser.add_argument("--manifest", help="hardening.toml (default: <repo-path>/hardening.toml)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any criterion is UNMET (default: always exit 0)",
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo_path).resolve()
    if not repo.is_dir():
        print(f"error: --repo-path is not a directory: {repo}", file=sys.stderr)
        return 2

    manifest = Path(args.manifest) if args.manifest else repo / "hardening.toml"
    if not manifest.is_file():
        print(f"error: manifest not found: {manifest}", file=sys.stderr)
        return 2

    tokens = render.load_manifest(manifest)
    slug = tokens.get("REPO_SLUG") or "{}/{}".format(
        tokens.get("PROJECT_ORG", "?"), tokens.get("PROJECT_NAME", "?")
    )

    results = run_checks(repo, args.tier, tokens, slug)
    counts = print_report(results, args.tier, slug)

    if args.strict and counts[UNMET]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
