# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Apply the GitHub-side hardening settings for a repo through the ``gh`` CLI.

This is the server-side companion to the file templates: the OpenSSF Best
Practices badge and a high Scorecard also depend on repository *settings* that
live only on GitHub (branch protection, security features, labels, the
two-person review collaborator). This script drives ``gh`` to put those in
place.

Hybrid safety model
-------------------
Every mutating action is **dry-run by default**. Without ``--apply`` the script
prints the exact ``gh``/``gh api`` command it *would* run, a one-line
consequence, and a rollback note -- and changes nothing. This makes the tool
safe to run blind against any repo to see the plan.

``--apply`` executes. Actions are graded by blast radius:

* **LOW** (``labels``, ``security-features``, and the read-only ``status``) run
  on ``--apply`` alone.
* **HIGH** (``add-reviewer``, ``branch-protection``) additionally require
  ``--yes`` *or* an interactive "type the repo name to confirm" prompt. They
  never execute on ``--apply`` alone -- granting write access or enabling
  ``enforce_admins`` can lock people out, so a second, deliberate signal is
  required.
* ``make-public`` is HIGH and stricter still: it refuses to execute without
  ``--yes`` (no interactive fallback) and always prints a "scan history for
  secrets first" reminder, because visibility is a one-way door for anything
  already committed.

Read-only ``status`` never mutates and ignores ``--apply``.

The script is stdlib-only and shells out to ``gh`` by design; the caller must
have ``gh`` installed and authenticated for the target repo.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys

# ---------------------------------------------------------------------------
# Desired state (the hardening baseline this script converges a repo toward).
# ---------------------------------------------------------------------------

DESIRED_LABELS: list[dict[str, str]] = [
    {"name": "good first issue", "color": "7057ff", "description": "Good for newcomers"},
    {"name": "help wanted", "color": "008672", "description": "Extra attention is welcome"},
    {"name": "dependencies", "color": "0366d6", "description": "Dependency updates"},
    {"name": "security", "color": "d73a4a", "description": "Security-relevant issue or fix"},
]

# Branch-protection target. Contexts are discovered at run time; everything else
# is fixed policy.
PROTECTED_BRANCH = "main"


# ---------------------------------------------------------------------------
# Command execution helpers.
# ---------------------------------------------------------------------------


def run(cmd: list[str], apply: bool, input_data: str | None = None) -> int:
    """Print (dry-run) or execute a ``gh``/``git`` command; return its exit code.

    In dry-run mode nothing is executed and ``0`` is returned. In apply mode the
    command runs, its stdout is echoed, and a non-zero exit is surfaced on
    stderr and returned to the caller so the process can exit non-zero.
    """
    printable = " ".join(shlex.quote(part) for part in cmd)
    if input_data is not None:
        printable += f"  <<'JSON'\n{input_data}\nJSON"

    if not apply:
        print(f"  DRY-RUN would run: {printable}")
        return 0

    print(f"  RUN: {printable}")
    try:
        proc = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        print(f"  ERROR: command not found ({exc})", file=sys.stderr)
        return 127

    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    if proc.returncode != 0:
        print(f"  ERROR (exit {proc.returncode}): {proc.stderr.rstrip()}", file=sys.stderr)
    return proc.returncode


def capture(cmd: list[str]) -> tuple[int, str, str]:
    """Run a read-only command, returning ``(returncode, stdout, stderr)``.

    Used for the ``status`` view and for reading current state before a PATCH so
    that mutating actions only touch real deltas. Never gated by ``--apply``.
    """
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        return 127, "", f"command not found ({exc})"
    return proc.returncode, proc.stdout, proc.stderr


def step(
    cmd: list[str],
    apply: bool,
    consequence: str,
    rollback: str,
    input_data: str | None = None,
) -> int:
    """Present one mutating step: consequence, rollback note, then run it."""
    print(f"  consequence: {consequence}")
    print(f"  rollback:    {rollback}")
    return run(cmd, apply, input_data=input_data)


# ---------------------------------------------------------------------------
# HIGH-risk confirmation gate.
# ---------------------------------------------------------------------------


def confirm_high(action: str, repo: str, args: argparse.Namespace) -> bool:
    """Return True if a HIGH-risk action may proceed under the current flags.

    Dry-run always proceeds (nothing executes). In apply mode this requires
    ``--yes`` or an interactive prompt where the operator types the repo name.
    """
    if not args.apply:
        return True
    if args.yes:
        return True
    print(f"  HIGH-RISK action '{action}' on {repo} requested with --apply but no --yes.")
    try:
        typed = input(f"  Type the repo name ({repo}) to confirm, anything else aborts: ")
    except EOFError:
        typed = ""
    if typed.strip() == repo:
        return True
    print("  aborted: confirmation did not match.", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# status (read-only)
# ---------------------------------------------------------------------------


def _read_lines(cmd: list[str]) -> list[str]:
    rc, out, _ = capture(cmd)
    if rc != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]


def gather_status(repo: str) -> dict[str, object]:
    """Collect current visibility, branch protection, labels, and collaborators."""
    status: dict[str, object] = {"repo": repo}

    rc, out, err = capture(["gh", "api", f"repos/{repo}", "--jq", ".visibility"])
    status["visibility"] = out.strip() if rc == 0 else f"unknown ({err.strip()})"

    rc, out, _ = capture(["gh", "api", f"repos/{repo}", "--jq", ".default_branch"])
    default_branch = out.strip() if rc == 0 else PROTECTED_BRANCH
    status["default_branch"] = default_branch

    rc, out, _ = capture(["gh", "api", f"repos/{repo}/branches/{default_branch}/protection"])
    if rc != 0:
        status["branch_protection"] = None
    else:
        try:
            prot = json.loads(out)
        except json.JSONDecodeError:
            prot = {}
        reviews = prot.get("required_pull_request_reviews", {}) or {}
        checks = prot.get("required_status_checks", {}) or {}
        status["branch_protection"] = {
            "enforce_admins": bool((prot.get("enforce_admins") or {}).get("enabled")),
            "required_approving_review_count": reviews.get("required_approving_review_count"),
            "require_code_owner_reviews": reviews.get("require_code_owner_reviews"),
            "dismiss_stale_reviews": reviews.get("dismiss_stale_reviews"),
            "require_last_push_approval": reviews.get("require_last_push_approval"),
            "required_linear_history": bool(
                (prot.get("required_linear_history") or {}).get("enabled")
            ),
            "required_conversation_resolution": bool(
                (prot.get("required_conversation_resolution") or {}).get("enabled")
            ),
            "required_status_checks_strict": checks.get("strict"),
            "required_status_checks_contexts": checks.get("contexts", []),
        }

    status["labels"] = _read_lines(
        ["gh", "api", "--paginate", f"repos/{repo}/labels", "--jq", ".[].name"]
    )
    status["collaborators"] = _read_lines(
        [
            "gh",
            "api",
            "--paginate",
            f"repos/{repo}/collaborators",
            "--jq",
            '.[] | .login + " (" + (.permissions | to_entries '
            '| map(select(.value)) | map(.key) | join(",")) + ")"',
        ]
    )
    return status


def cmd_status(args: argparse.Namespace) -> int:
    status = gather_status(args.repo)
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0

    print(f"repo:              {status['repo']}")
    print(f"visibility:        {status['visibility']}")
    print(f"default_branch:    {status['default_branch']}")
    prot = status["branch_protection"]
    if prot is None:
        print("branch_protection: NONE (main is unprotected)")
    else:
        print("branch_protection:")
        for key, value in prot.items():  # type: ignore[union-attr]
            print(f"    {key}: {value}")
    labels = status["labels"]
    assert isinstance(labels, list)
    print(f"labels ({len(labels)}):    {', '.join(labels) if labels else '(none)'}")
    collabs = status["collaborators"]
    assert isinstance(collabs, list)
    print(f"collaborators ({len(collabs)}):")
    for line in collabs:
        print(f"    {line}")
    return 0


# ---------------------------------------------------------------------------
# labels (LOW)
# ---------------------------------------------------------------------------


def cmd_labels(args: argparse.Namespace) -> int:
    repo = args.repo
    existing = {
        name.lower()
        for name in _read_lines(
            ["gh", "api", "--paginate", f"repos/{repo}/labels", "--jq", ".[].name"]
        )
    }
    worst = 0
    for label in DESIRED_LABELS:
        name = label["name"]
        if name.lower() in existing:
            print(f"label '{name}': present, skipping")
            continue
        print(f"label '{name}': missing")
        cmd = [
            "gh",
            "api",
            "-X",
            "POST",
            f"repos/{repo}/labels",
            "-f",
            f"name={name}",
            "-f",
            f"color={label['color']}",
            "-f",
            f"description={label['description']}",
        ]
        rc = step(
            cmd,
            args.apply,
            consequence=f"creates the '{name}' label on {repo}",
            rollback=f"gh api -X DELETE repos/{repo}/labels/{shlex.quote(name)}",
        )
        worst = max(worst, rc)
    return worst


# ---------------------------------------------------------------------------
# security-features (LOW / MED)
# ---------------------------------------------------------------------------


def cmd_security_features(args: argparse.Namespace) -> int:
    repo = args.repo
    worst = 0

    worst = max(
        worst,
        step(
            ["gh", "api", "-X", "PUT", f"repos/{repo}/vulnerability-alerts"],
            args.apply,
            consequence="enables Dependabot vulnerability alerts",
            rollback=f"gh api -X DELETE repos/{repo}/vulnerability-alerts",
        ),
    )

    worst = max(
        worst,
        step(
            ["gh", "api", "-X", "PUT", f"repos/{repo}/automated-security-fixes"],
            args.apply,
            consequence="enables automated Dependabot security-fix PRs",
            rollback=f"gh api -X DELETE repos/{repo}/automated-security-fixes",
        ),
    )

    body = json.dumps({"security_and_analysis": {"secret_scanning": {"status": "enabled"}}})
    worst = max(
        worst,
        step(
            ["gh", "api", "-X", "PATCH", f"repos/{repo}", "--input", "-"],
            args.apply,
            consequence="enables secret scanning (public repos / GHAS-enabled private repos only)",
            rollback="re-PATCH security_and_analysis.secret_scanning.status=disabled",
            input_data=body,
        ),
    )
    return worst


# ---------------------------------------------------------------------------
# add-reviewer (HIGH)
# ---------------------------------------------------------------------------


def cmd_add_reviewer(args: argparse.Namespace) -> int:
    repo = args.repo
    user = args.user
    if not confirm_high("add-reviewer", repo, args):
        return 3
    cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        f"repos/{repo}/collaborators/{user}",
        "-f",
        "permission=push",
    ]
    return step(
        cmd,
        args.apply,
        consequence=f"grants '{user}' WRITE access to {repo} (invitation until accepted)",
        rollback=f"gh api -X DELETE repos/{repo}/collaborators/{user}",
    )


# ---------------------------------------------------------------------------
# branch-protection (HIGH)
# ---------------------------------------------------------------------------


# Checks that monitor repository posture on push/schedule but do NOT run on
# pull_request events. Requiring one as a status check hangs every PR forever on
# an "Expected" check that never reports (OpenSSF Scorecard is the canonical
# case), so they are excluded from the discovered required contexts.
_NON_PR_CHECK_SUBSTRINGS = ("scorecard",)


def is_pr_status_check(name: str) -> bool:
    """False for posture checks that never run on pull_request (e.g. Scorecard)."""
    lowered = name.lower()
    return not any(marker in lowered for marker in _NON_PR_CHECK_SUBSTRINGS)


def discover_status_checks(repo: str) -> list[str]:
    """Return the distinct check-run names on the default branch's latest commit.

    These become the required status-check contexts, minus posture-only checks
    that never run on pull_request (see ``is_pr_status_check``) — requiring those
    would block every PR indefinitely. If none can be found the caller falls back
    to strict mode with an empty context list and a note.
    """
    rc, out, _ = capture(
        [
            "gh",
            "api",
            f"repos/{repo}/commits/{PROTECTED_BRANCH}/check-runs",
            "--jq",
            ".check_runs[].name",
        ]
    )
    if rc != 0:
        return []
    seen: list[str] = []
    for name in out.splitlines():
        name = name.strip()
        if name and name not in seen and is_pr_status_check(name):
            seen.append(name)
    return seen


def desired_protection(contexts: list[str]) -> dict[str, object]:
    return {
        "required_status_checks": {"strict": True, "contexts": contexts},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "require_code_owner_reviews": True,
            "dismiss_stale_reviews": True,
            "require_last_push_approval": True,
        },
        "restrictions": None,
        "required_linear_history": True,
        "required_conversation_resolution": True,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }


def _current_protection_shape(repo: str) -> dict[str, object] | None:
    rc, out, _ = capture(["gh", "api", f"repos/{repo}/branches/{PROTECTED_BRANCH}/protection"])
    if rc != 0:
        return None
    try:
        prot = json.loads(out)
    except json.JSONDecodeError:
        return None
    reviews = prot.get("required_pull_request_reviews", {}) or {}
    checks = prot.get("required_status_checks", {}) or {}
    return {
        "required_status_checks": {
            "strict": checks.get("strict"),
            "contexts": sorted(checks.get("contexts", [])),
        },
        "enforce_admins": bool((prot.get("enforce_admins") or {}).get("enabled")),
        "required_pull_request_reviews": {
            "required_approving_review_count": reviews.get("required_approving_review_count"),
            "require_code_owner_reviews": reviews.get("require_code_owner_reviews"),
            "dismiss_stale_reviews": reviews.get("dismiss_stale_reviews"),
            "require_last_push_approval": reviews.get("require_last_push_approval"),
        },
        "required_linear_history": bool((prot.get("required_linear_history") or {}).get("enabled")),
        "required_conversation_resolution": bool(
            (prot.get("required_conversation_resolution") or {}).get("enabled")
        ),
        "allow_force_pushes": bool((prot.get("allow_force_pushes") or {}).get("enabled")),
        "allow_deletions": bool((prot.get("allow_deletions") or {}).get("enabled")),
    }


def _matches(current: dict[str, object] | None, desired: dict[str, object]) -> bool:
    """Idempotency check: is current already at (or above) the desired shape?"""
    if current is None:
        return False
    want = dict(desired)
    want.pop("restrictions", None)
    want_checks = dict(want["required_status_checks"])  # type: ignore[arg-type]
    want_checks["contexts"] = sorted(want_checks["contexts"])  # type: ignore[index]
    want["required_status_checks"] = want_checks
    return current == want


def cmd_branch_protection(args: argparse.Namespace) -> int:
    repo = args.repo
    if not confirm_high("branch-protection", repo, args):
        return 3

    contexts = discover_status_checks(repo)
    if contexts:
        print(f"discovered status-check contexts: {', '.join(contexts)}")
    else:
        print(
            "note: no status-check contexts discovered from recent runs; "
            "applying strict mode with an empty context list -- fill contexts "
            "in once CI has run at least once on main."
        )

    desired = desired_protection(contexts)
    current = _current_protection_shape(repo)
    if _matches(current, desired):
        print(f"branch protection on '{PROTECTED_BRANCH}' already compliant -- no change.")
        return 0
    if current is None:
        print(f"'{PROTECTED_BRANCH}' is currently unprotected -- will apply full policy.")
    else:
        print(f"'{PROTECTED_BRANCH}' protection differs from target -- will re-apply policy.")

    body = json.dumps(desired, indent=2)
    cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        f"repos/{repo}/branches/{PROTECTED_BRANCH}/protection",
        "--input",
        "-",
    ]
    return step(
        cmd,
        args.apply,
        consequence=(
            "requires 1 code-owner PR approval + strict status checks on "
            f"'{PROTECTED_BRANCH}' and enforces it on admins too (enforce_admins:true "
            "can lock out the sole maintainer)"
        ),
        rollback=f"gh api -X DELETE repos/{repo}/branches/{PROTECTED_BRANCH}/protection",
        input_data=body,
    )


# ---------------------------------------------------------------------------
# make-public (HIGH, --yes only)
# ---------------------------------------------------------------------------


def cmd_make_public(args: argparse.Namespace) -> int:
    repo = args.repo
    print(
        "WARNING: making a repo public exposes its ENTIRE git history. Scan the "
        "history for secrets FIRST (e.g. gitleaks/trufflehog over all refs); a "
        "leaked credential in any past commit is public the instant you flip this."
    )
    if args.apply and not args.yes:
        print(
            "  refusing to make-public without --yes (no interactive fallback for this action).",
            file=sys.stderr,
        )
        return 3
    cmd = ["gh", "api", "-X", "PATCH", f"repos/{repo}", "-f", "visibility=public"]
    return step(
        cmd,
        args.apply,
        consequence=f"flips {repo} to PUBLIC (history and all)",
        rollback=f"gh api -X PATCH repos/{repo} -f visibility=private",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", required=True, help="target repo as OWNER/NAME")
    common.add_argument(
        "--apply",
        action="store_true",
        help="execute (default is dry-run: print commands, change nothing)",
    )
    common.add_argument(
        "--yes",
        action="store_true",
        help="confirm HIGH-risk actions non-interactively",
    )

    parser = argparse.ArgumentParser(
        description="Apply GitHub-side hardening settings via gh (dry-run by default)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", parents=[common], help="read-only: print current settings")
    p_status.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p_status.set_defaults(func=cmd_status)

    p_labels = sub.add_parser(
        "labels", parents=[common], help="create standard labels if missing (LOW)"
    )
    p_labels.set_defaults(func=cmd_labels)
    p_sec = sub.add_parser(
        "security-features", parents=[common], help="enable alerts/fixes/secret-scanning (LOW/MED)"
    )
    p_sec.set_defaults(func=cmd_security_features)

    p_rev = sub.add_parser("add-reviewer", parents=[common], help="add a write collaborator (HIGH)")
    p_rev.add_argument("--user", required=True, help="GitHub login to grant write access")
    p_rev.set_defaults(func=cmd_add_reviewer)

    sub.add_parser(
        "branch-protection", parents=[common], help="apply main-branch protection policy (HIGH)"
    ).set_defaults(func=cmd_branch_protection)
    sub.add_parser(
        "make-public", parents=[common], help="flip visibility to public (HIGH, --yes required)"
    ).set_defaults(func=cmd_make_public)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
