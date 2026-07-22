# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""GitHub-settings hardening tests.

The invariant under test: dry-run is the default and NEVER shells out; mutating
subcommands print the exact command they would run plus a consequence/rollback
note; HIGH-risk actions refuse to execute under ``--apply`` without ``--yes``.
No real ``gh`` is ever invoked — the subprocess boundary is patched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gh_settings  # noqa: E402


class _Proc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _ns(**kw: object) -> argparse.Namespace:
    kw.setdefault("apply", False)
    kw.setdefault("yes", False)
    return argparse.Namespace(**kw)


@pytest.fixture(autouse=True)
def _no_real_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if any test path executes a real subprocess without opting in."""

    def _boom(*a: object, **k: object) -> None:
        raise AssertionError("subprocess.run called unexpectedly (dry-run must not execute)")

    monkeypatch.setattr(gh_settings.subprocess, "run", _boom)


# --- run() -----------------------------------------------------------------


def test_run_dryrun_prints_and_does_not_execute(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.run(["gh", "api", "repos/o/r"], apply=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN would run:" in out
    assert "gh api repos/o/r" in out


def test_run_dryrun_shows_heredoc_input(capsys: pytest.CaptureFixture[str]) -> None:
    gh_settings.run(["gh", "api", "x", "--input", "-"], apply=False, input_data='{"a": 1}')
    out = capsys.readouterr().out
    assert "JSON" in out
    assert '{"a": 1}' in out


def test_run_apply_executes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings.subprocess, "run", lambda *a, **k: _Proc(0, "ok output"))
    rc = gh_settings.run(["gh", "api", "x"], apply=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "RUN:" in out
    assert "ok output" in out


def test_run_apply_surfaces_nonzero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings.subprocess, "run", lambda *a, **k: _Proc(1, "", "boom"))
    rc = gh_settings.run(["gh", "api", "x"], apply=True)
    assert rc == 1
    assert "ERROR (exit 1)" in capsys.readouterr().err


def test_run_apply_command_not_found(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise FileNotFoundError("gh")

    monkeypatch.setattr(gh_settings.subprocess, "run", _raise)
    rc = gh_settings.run(["gh", "api", "x"], apply=True)
    assert rc == 127
    assert "command not found" in capsys.readouterr().err


# --- capture() -------------------------------------------------------------


def test_capture_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_settings.subprocess, "run", lambda *a, **k: _Proc(0, "out", "err"))
    assert gh_settings.capture(["gh", "api", "x"]) == (0, "out", "err")


def test_capture_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise FileNotFoundError("gh")

    monkeypatch.setattr(gh_settings.subprocess, "run", _raise)
    rc, out, err = gh_settings.capture(["gh", "api", "x"])
    assert rc == 127
    assert out == ""
    assert "command not found" in err


# --- confirm_high() --------------------------------------------------------


def test_confirm_high_dryrun_always_true() -> None:
    assert gh_settings.confirm_high("add-reviewer", "o/r", _ns(apply=False)) is True


def test_confirm_high_yes_flag_true() -> None:
    assert gh_settings.confirm_high("add-reviewer", "o/r", _ns(apply=True, yes=True)) is True


def test_confirm_high_interactive_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "o/r")
    assert gh_settings.confirm_high("branch-protection", "o/r", _ns(apply=True)) is True


def test_confirm_high_interactive_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt: "wrong")
    assert gh_settings.confirm_high("branch-protection", "o/r", _ns(apply=True)) is False


def test_confirm_high_eof_aborts(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise)
    assert gh_settings.confirm_high("branch-protection", "o/r", _ns(apply=True)) is False


# --- step() ----------------------------------------------------------------


def test_step_prints_consequence_and_rollback(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.step(["gh", "api", "x"], apply=False, consequence="does X", rollback="undo X")
    assert rc == 0
    out = capsys.readouterr().out
    assert "consequence: does X" in out
    assert "rollback:    undo X" in out


# --- labels (LOW) ----------------------------------------------------------


def test_cmd_labels_dryrun_plans_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # "security" already present; the other three are missing.
    monkeypatch.setattr(gh_settings, "_read_lines", lambda cmd: ["security"])
    rc = gh_settings.cmd_labels(_ns(repo="o/r"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "label 'security': present, skipping" in out
    assert "label 'good first issue': missing" in out
    assert "DRY-RUN would run:" in out  # never executed


# --- security-features (LOW/MED) ------------------------------------------


def test_cmd_security_features_dryrun(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.cmd_security_features(_ns(repo="o/r"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "vulnerability-alerts" in out
    assert "automated-security-fixes" in out
    assert "secret_scanning" in out


# --- add-reviewer (HIGH) ---------------------------------------------------


def test_cmd_add_reviewer_dryrun_plans(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.cmd_add_reviewer(_ns(repo="o/r", user="bob"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "collaborators/bob" in out
    assert "WRITE access" in out


def test_cmd_add_reviewer_apply_without_yes_refuses(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # No --yes and no TTY: input() raises EOFError → confirm_high returns False.
    def _raise(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise)
    rc = gh_settings.cmd_add_reviewer(_ns(repo="o/r", user="bob", apply=True))
    assert rc == 3  # refused, and subprocess never ran (autouse guard proves it)
    assert "aborted" in capsys.readouterr().err


# --- branch-protection (HIGH) ---------------------------------------------


def test_desired_protection_shape() -> None:
    d = gh_settings.desired_protection(["ci / build"])
    assert d["enforce_admins"] is True
    assert d["required_status_checks"] == {"strict": True, "contexts": ["ci / build"]}
    reviews = d["required_pull_request_reviews"]
    assert reviews["require_code_owner_reviews"] is True
    assert reviews["required_approving_review_count"] == 1


def test_matches_idempotency() -> None:
    desired = gh_settings.desired_protection(["b", "a"])
    current = {
        "required_status_checks": {"strict": True, "contexts": ["a", "b"]},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "require_code_owner_reviews": True,
            "dismiss_stale_reviews": True,
            "require_last_push_approval": True,
        },
        "required_linear_history": True,
        "required_conversation_resolution": True,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    assert gh_settings._matches(current, desired) is True
    assert gh_settings._matches(None, desired) is False
    drift = dict(current)
    drift["enforce_admins"] = False
    assert gh_settings._matches(drift, desired) is False


def test_discover_status_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_settings, "capture", lambda cmd: (0, "ci\nci\nlint\n", ""))
    assert gh_settings.discover_status_checks("o/r") == ["ci", "lint"]  # de-duped, ordered
    monkeypatch.setattr(gh_settings, "capture", lambda cmd: (1, "", "err"))
    assert gh_settings.discover_status_checks("o/r") == []


def test_current_protection_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        {
            "required_status_checks": {"strict": True, "contexts": ["a"]},
            "enforce_admins": {"enabled": True},
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": True,
                "dismiss_stale_reviews": True,
                "require_last_push_approval": True,
            },
        }
    )
    monkeypatch.setattr(gh_settings, "capture", lambda cmd: (0, payload, ""))
    shape = gh_settings._current_protection_shape("o/r")
    assert shape is not None
    assert shape["enforce_admins"] is True

    monkeypatch.setattr(gh_settings, "capture", lambda cmd: (1, "", ""))
    assert gh_settings._current_protection_shape("o/r") is None

    monkeypatch.setattr(gh_settings, "capture", lambda cmd: (0, "not json", ""))
    assert gh_settings._current_protection_shape("o/r") is None


def test_cmd_branch_protection_already_compliant(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "discover_status_checks", lambda repo: ["ci"])
    # Build a "current" that equals desired for contexts ["ci"].
    desired = gh_settings.desired_protection(["ci"])
    current = {
        "required_status_checks": {"strict": True, "contexts": ["ci"]},
        "enforce_admins": True,
        "required_pull_request_reviews": desired["required_pull_request_reviews"],
        "required_linear_history": True,
        "required_conversation_resolution": True,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    monkeypatch.setattr(gh_settings, "_current_protection_shape", lambda repo: current)
    rc = gh_settings.cmd_branch_protection(_ns(repo="o/r", apply=False, yes=False))
    assert rc == 0
    assert "already compliant" in capsys.readouterr().out


def test_cmd_branch_protection_unprotected_plans(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "discover_status_checks", lambda repo: [])
    monkeypatch.setattr(gh_settings, "_current_protection_shape", lambda repo: None)
    rc = gh_settings.cmd_branch_protection(_ns(repo="o/r", apply=False, yes=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "currently unprotected" in out
    assert "no status-check contexts discovered" in out
    assert "DRY-RUN would run:" in out


def test_cmd_branch_protection_differs_replans(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "discover_status_checks", lambda repo: ["ci"])
    monkeypatch.setattr(
        gh_settings, "_current_protection_shape", lambda repo: {"enforce_admins": False}
    )
    rc = gh_settings.cmd_branch_protection(_ns(repo="o/r", apply=False, yes=False))
    assert rc == 0
    assert "differs from target" in capsys.readouterr().out


# --- make-public (HIGH, --yes only) ---------------------------------------


def test_cmd_make_public_dryrun_warns(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.cmd_make_public(_ns(repo="o/r"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "Scan the" in out
    assert "DRY-RUN would run:" in out


def test_cmd_make_public_apply_without_yes_refuses(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.cmd_make_public(_ns(repo="o/r", apply=True, yes=False))
    assert rc == 3
    assert "refusing to make-public without --yes" in capsys.readouterr().err


# --- status (read-only) ----------------------------------------------------


def _fake_capture_factory() -> object:
    prot = json.dumps(
        {
            "enforce_admins": {"enabled": True},
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "require_code_owner_reviews": True,
                "dismiss_stale_reviews": True,
                "require_last_push_approval": True,
            },
            "required_linear_history": {"enabled": True},
            "required_conversation_resolution": {"enabled": True},
            "required_status_checks": {"strict": True, "contexts": ["ci"]},
        }
    )

    def _cap(cmd: list[str]) -> tuple[int, str, str]:
        joined = " ".join(cmd)
        if joined.endswith(".visibility"):
            return 0, "public\n", ""
        if joined.endswith(".default_branch"):
            return 0, "main\n", ""
        if "protection" in joined:
            return 0, prot, ""
        if "/labels" in joined:
            return 0, "bug\nsecurity\n", ""
        if "/collaborators" in joined:
            return 0, "alice (admin)\n", ""
        return 1, "", "err"

    return _cap


def test_gather_status_full(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_settings, "capture", _fake_capture_factory())
    status = gh_settings.gather_status("o/r")
    assert status["visibility"] == "public"
    assert status["default_branch"] == "main"
    prot = status["branch_protection"]
    assert isinstance(prot, dict)
    assert prot["enforce_admins"] is True
    assert prot["required_status_checks_contexts"] == ["ci"]
    assert status["labels"] == ["bug", "security"]
    assert status["collaborators"] == ["alice (admin)"]


def test_gather_status_no_protection(monkeypatch: pytest.MonkeyPatch) -> None:
    def _cap(cmd: list[str]) -> tuple[int, str, str]:
        joined = " ".join(cmd)
        if joined.endswith(".visibility"):
            return 0, "public\n", ""
        if joined.endswith(".default_branch"):
            return 0, "main\n", ""
        return 1, "", "no protection"

    monkeypatch.setattr(gh_settings, "capture", _cap)
    status = gh_settings.gather_status("o/r")
    assert status["branch_protection"] is None


def test_cmd_status_text(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "capture", _fake_capture_factory())
    rc = gh_settings.cmd_status(_ns(repo="o/r", json=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "visibility:        public" in out
    assert "branch_protection:" in out
    assert "enforce_admins" in out


def test_cmd_status_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "capture", _fake_capture_factory())
    rc = gh_settings.cmd_status(_ns(repo="o/r", json=True))
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["repo"] == "o/r"
    assert parsed["visibility"] == "public"


def test_cmd_status_text_no_protection(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _cap(cmd: list[str]) -> tuple[int, str, str]:
        joined = " ".join(cmd)
        if joined.endswith(".visibility"):
            return 0, "public\n", ""
        if joined.endswith(".default_branch"):
            return 0, "main\n", ""
        return 1, "", ""

    monkeypatch.setattr(gh_settings, "capture", _cap)
    gh_settings.cmd_status(_ns(repo="o/r", json=False))
    assert "NONE (main is unprotected)" in capsys.readouterr().out


# --- CLI dispatch ----------------------------------------------------------


def test_main_dispatches_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gh_settings, "gather_status", lambda repo: {"repo": repo})
    rc = gh_settings.main(["status", "--repo", "o/r", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["repo"] == "o/r"


def test_main_dispatches_make_public_dryrun(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gh_settings.main(["make-public", "--repo", "o/r"])
    assert rc == 0
    assert "WARNING" in capsys.readouterr().out


def test_build_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        gh_settings.main([])


def test_is_pr_status_check_excludes_scorecard() -> None:
    assert gh_settings.is_pr_status_check("Test (Python 3.12)")
    assert gh_settings.is_pr_status_check("Lint")
    assert not gh_settings.is_pr_status_check("Scorecard analysis")
    assert not gh_settings.is_pr_status_check("OpenSSF Scorecard")


def test_discover_status_checks_drops_scorecard(monkeypatch: pytest.MonkeyPatch) -> None:
    # Scorecard runs on push/schedule, never on pull_request — requiring it as a
    # status check would hang every PR, so it must be filtered from the contexts.
    monkeypatch.setattr(
        gh_settings,
        "capture",
        lambda cmd: (0, "Lint\nScorecard analysis\nTest (Python 3.12)\n", ""),
    )
    assert gh_settings.discover_status_checks("o/r") == ["Lint", "Test (Python 3.12)"]
