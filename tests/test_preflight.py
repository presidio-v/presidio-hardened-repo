# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Gap-analysis checker tests.

Exercises the pure criterion checks (file-exists + FILL detection, coverage.json
parsing vs a tier floor, badge registration, atheris literal detection, SPDX
sampling) and confirms the gh-backed checks degrade to NEEDS-HUMAN-EVIDENCE when
gh is unavailable. No real ``gh`` is ever invoked.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import preflight  # noqa: E402

MANIFEST = """\
[project]
name = "acme-lib"
org = "acme-v"

[people]
maintainer = "alice"
reviewer = "bob"

[legal]
copyright_holder = "Acme Inc"
license = "MIT"

[badge]
bestpractices_id = 4242
"""

# All passing + silver docs, so a fully-populated repo scores MET across files.
_DOC_NAMES = [
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "SEMVER.md",
    "CHANGELOG.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/workflows/scorecard.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/ci.yml",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "ARCHITECTURE.md",
    "ASSURANCE.md",
    "allowed_signers",
]


def _make_repo(root: Path, *, docs: bool = True) -> Path:
    (root / "hardening.toml").write_text(MANIFEST, encoding="utf-8")
    if docs:
        for rel in _DOC_NAMES:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {Path(rel).name}\nclean content\n", encoding="utf-8")
        # The CI workflow must actually run the test suite for the CI check.
        (root / ".github" / "workflows" / "ci.yml").write_text(
            "name: CI\njobs:\n  test:\n    steps:\n      - run: pytest tests/\n",
            encoding="utf-8",
        )
    return root


@pytest.fixture
def tokens(tmp_path: Path) -> dict[str, str]:
    m = tmp_path / "manifest.toml"
    m.write_text(MANIFEST, encoding="utf-8")
    return preflight.render.load_manifest(m)


# --- tier ordering ---------------------------------------------------------


def test_tier_applies() -> None:
    assert preflight._tier_applies("passing", "silver")
    assert preflight._tier_applies("silver", "silver")
    assert not preflight._tier_applies("silver", "passing")


# --- file checks -----------------------------------------------------------


def test_check_files_all_met(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    results = preflight.check_files(repo, "silver")
    assert all(r.status == preflight.MET for r in results)
    # silver pulls in more criteria than passing.
    assert len(results) > len(preflight.check_files(repo, "passing"))


def test_check_files_missing_is_unmet(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, docs=False)
    results = preflight.check_files(repo, "passing")
    assert results
    assert all(r.status == preflight.UNMET for r in results)
    assert any("missing" in r.reason for r in results)


def test_check_files_open_fill_marker_is_unmet(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "ARCHITECTURE.md").write_text("# Arch\n<!-- FILL:components -->\n", encoding="utf-8")
    results = preflight.check_files(repo, "silver")
    arch = next(r for r in results if r.criterion == "documentation_architecture")
    assert arch.status == preflight.UNMET
    assert "FILL" in arch.reason


# --- continuous integration (Fix 2a: any test-running workflow) ------------


def _write_workflow(repo: Path, name: str, content: str) -> None:
    d = repo / ".github" / "workflows"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(content, encoding="utf-8")


def test_ci_no_workflows_dir_is_unmet(tmp_path: Path) -> None:
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.UNMET
    assert "no .github/workflows" in result.reason


def test_ci_empty_workflows_dir_is_unmet(tmp_path: Path) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.UNMET
    assert "no workflow files" in result.reason


def test_ci_pytest_yml_is_met(tmp_path: Path) -> None:
    # Flagship ikigov-assess uses pytest.yml, not ci.yml — must count as MET.
    _write_workflow(
        tmp_path, "pytest.yml", "name: Tests\njobs:\n  run:\n    steps:\n      - run: pytest -q\n"
    )
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.MET
    assert "pytest.yml" in result.reason


def test_ci_test_job_name_is_met(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "build.yaml",
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make check\n",
    )
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.MET
    assert "build.yaml" in result.reason


def test_ci_only_scorecard_is_unmet(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "scorecard.yml",
        "name: Scorecard\njobs:\n  analysis:\n    runs-on: ubuntu-latest\n",
    )
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.UNMET
    assert "scorecard.yml" in result.reason


def test_ci_ubuntu_latest_is_not_a_false_positive(tmp_path: Path) -> None:
    # 'ubuntu-latest' contains the substring 'test' but not the whole word.
    _write_workflow(
        tmp_path,
        "lint.yml",
        "jobs:\n  lint:\n    runs-on: ubuntu-latest\n    steps:\n      - run: ruff check .\n",
    )
    (result,) = preflight.check_continuous_integration(tmp_path)
    assert result.status == preflight.UNMET


# --- SPDX sampling ---------------------------------------------------------


def test_check_spdx_no_src_is_human(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (result,) = preflight.check_spdx_headers(repo)
    assert result.status == preflight.HUMAN
    assert "no src/" in result.reason


def test_check_spdx_no_py_is_human(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "src").mkdir()
    (result,) = preflight.check_spdx_headers(repo)
    assert result.status == preflight.HUMAN


def test_check_spdx_all_headed_is_met(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    src = repo / "src" / "pkg"
    src.mkdir(parents=True)
    (src / "a.py").write_text("# SPDX-License-Identifier: MIT\nx = 1\n", encoding="utf-8")
    (result,) = preflight.check_spdx_headers(repo)
    assert result.status == preflight.MET


def test_check_spdx_missing_is_unmet(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    src = repo / "src" / "pkg"
    src.mkdir(parents=True)
    (src / "a.py").write_text("# SPDX-License-Identifier: MIT\nx = 1\n", encoding="utf-8")
    (src / "b.py").write_text("x = 2\n", encoding="utf-8")
    (result,) = preflight.check_spdx_headers(repo)
    assert result.status == preflight.UNMET
    assert "b.py" in result.reason


# --- fuzzing ---------------------------------------------------------------


def test_check_fuzzing_no_dir(tmp_path: Path) -> None:
    (result,) = preflight.check_fuzzing(tmp_path)
    assert result.status == preflight.UNMET


def test_check_fuzzing_atheris_present(tmp_path: Path) -> None:
    fuzz = tmp_path / "fuzz"
    fuzz.mkdir()
    (fuzz / "fuzz_x.py").write_text("import atheris\nimport sys\n", encoding="utf-8")
    (result,) = preflight.check_fuzzing(tmp_path)
    assert result.status == preflight.MET
    assert "import atheris" in result.reason


def test_check_fuzzing_dir_without_harness(tmp_path: Path) -> None:
    fuzz = tmp_path / "fuzz"
    fuzz.mkdir()
    (fuzz / "readme.txt").write_text("no harness yet\n", encoding="utf-8")
    (result,) = preflight.check_fuzzing(tmp_path)
    assert result.status == preflight.UNMET


# --- coverage --------------------------------------------------------------


def _write_cov(repo: Path, totals: dict[str, object]) -> None:
    (repo / "coverage.json").write_text(json.dumps({"totals": totals}), encoding="utf-8")


def test_check_coverage_absent_is_human(tmp_path: Path) -> None:
    (result,) = preflight.check_coverage(tmp_path, "silver")
    assert result.status == preflight.HUMAN


def test_check_coverage_above_floor_is_met(tmp_path: Path) -> None:
    _write_cov(tmp_path, {"percent_covered": 85.0, "num_branches": 100, "covered_branches": 90})
    (result,) = preflight.check_coverage(tmp_path, "silver")
    assert result.status == preflight.MET
    assert "branch 90.0%" in result.reason


def test_check_coverage_below_floor_is_unmet(tmp_path: Path) -> None:
    _write_cov(tmp_path, {"percent_covered": 70.0})
    (result,) = preflight.check_coverage(tmp_path, "silver")
    assert result.status == preflight.UNMET


def test_check_coverage_passing_floor_lower(tmp_path: Path) -> None:
    _write_cov(tmp_path, {"percent_covered": 65.0})
    # 65% clears the passing floor (60) but not silver (80).
    assert preflight.check_coverage(tmp_path, "passing")[0].status == preflight.MET
    assert preflight.check_coverage(tmp_path, "silver")[0].status == preflight.UNMET


def test_check_coverage_no_percent_is_human(tmp_path: Path) -> None:
    _write_cov(tmp_path, {"num_branches": 10})
    (result,) = preflight.check_coverage(tmp_path, "silver")
    assert result.status == preflight.HUMAN


def test_check_coverage_unreadable_is_human(tmp_path: Path) -> None:
    (tmp_path / "coverage.json").write_text("{not json", encoding="utf-8")
    (result,) = preflight.check_coverage(tmp_path, "silver")
    assert result.status == preflight.HUMAN


# --- registration ----------------------------------------------------------


def test_check_registration_set(tokens: dict[str, str]) -> None:
    (result,) = preflight.check_registration(tokens)
    assert result.status == preflight.MET
    assert "4242" in result.reason


def test_check_registration_zero_is_unmet() -> None:
    (result,) = preflight.check_registration({"BADGE_BESTPRACTICES_ID": "0"})
    assert result.status == preflight.UNMET


def test_check_registration_missing_is_unmet() -> None:
    (result,) = preflight.check_registration({})
    assert result.status == preflight.UNMET


# --- human criteria --------------------------------------------------------


def test_human_criteria_tier_scoped() -> None:
    passing = preflight.human_criteria("passing")
    silver = preflight.human_criteria("silver")
    assert all(r.status == preflight.HUMAN for r in silver)
    assert len(silver) > len(passing)


# --- gh helpers (subprocess boundary, patched) -----------------------------


class _Proc:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def test_gh_returns_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight.subprocess, "run", lambda *a, **k: _Proc(0, "hi"))
    assert preflight._gh(["api", "x"]) == (0, "hi")


def test_gh_missing_binary_is_127(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(preflight.subprocess, "run", _raise)
    assert preflight._gh(["api", "x"]) == (127, "")


def test_gh_timeout_is_124(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*a: object, **k: object) -> None:
        raise subprocess.TimeoutExpired(cmd="gh", timeout=30)

    monkeypatch.setattr(preflight.subprocess, "run", _raise)
    assert preflight._gh(["api", "x"]) == (124, "")


def test_gh_json_parses_and_degrades(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh", lambda args: (0, '{"a": 1}'))
    assert preflight._gh_json(["x"]) == {"a": 1}
    monkeypatch.setattr(preflight, "_gh", lambda args: (1, ""))
    assert preflight._gh_json(["x"]) is None
    monkeypatch.setattr(preflight, "_gh", lambda args: (0, "not json"))
    assert preflight._gh_json(["x"]) is None


# --- individual remote checks (patched _gh_json / _gh) ---------------------


def test_check_repo_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_json", lambda a: {"visibility": "public"})
    assert preflight.check_repo_public("o/r")[0].status == preflight.MET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: {"private": True})
    assert preflight.check_repo_public("o/r")[0].status == preflight.UNMET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    assert preflight.check_repo_public("o/r")[0].status == preflight.HUMAN


def test_check_branch_protection(monkeypatch: pytest.MonkeyPatch) -> None:
    good = {
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "require_code_owner_reviews": True,
        },
        "enforce_admins": {"enabled": True},
    }
    monkeypatch.setattr(preflight, "_gh_json", lambda a: good)
    assert preflight.check_branch_protection("o/r")[0].status == preflight.MET

    monkeypatch.setattr(preflight, "_gh_json", lambda a: {})
    r = preflight.check_branch_protection("o/r")[0]
    assert r.status == preflight.UNMET
    assert "no required approving review" in r.reason

    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    assert preflight.check_branch_protection("o/r")[0].status == preflight.HUMAN


def test_check_good_first_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_json", lambda a: [{"name": "Good First Issue"}])
    assert preflight.check_good_first_issue("o/r")[0].status == preflight.MET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: [{"name": "bug"}])
    assert preflight.check_good_first_issue("o/r")[0].status == preflight.UNMET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    assert preflight.check_good_first_issue("o/r")[0].status == preflight.HUMAN


def test_check_reviewer_collaborator(monkeypatch: pytest.MonkeyPatch) -> None:
    assert preflight.check_reviewer_collaborator("o/r", "")[0].status == preflight.HUMAN
    monkeypatch.setattr(preflight, "_gh", lambda a: (0, ""))
    assert preflight.check_reviewer_collaborator("o/r", "bob")[0].status == preflight.MET
    monkeypatch.setattr(preflight, "_gh", lambda a: (127, ""))
    assert preflight.check_reviewer_collaborator("o/r", "bob")[0].status == preflight.HUMAN
    monkeypatch.setattr(preflight, "_gh", lambda a: (1, ""))
    assert preflight.check_reviewer_collaborator("o/r", "bob")[0].status == preflight.UNMET


def test_check_tag_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    assert preflight.check_tag_verification("o/r")[0].status == preflight.HUMAN

    monkeypatch.setattr(preflight, "_gh_json", lambda a: [])
    assert preflight.check_tag_verification("o/r")[0].status == preflight.UNMET

    # lightweight tags only (object.type == commit)
    monkeypatch.setattr(
        preflight, "_gh_json", lambda a: [{"object": {"type": "commit", "sha": "abc"}}]
    )
    assert preflight.check_tag_verification("o/r")[0].status == preflight.UNMET

    # annotated tag → second call fetches the tag object and its verification.
    refs = [{"object": {"type": "tag", "sha": "deadbeef"}}]
    calls = {"n": 0}

    def _fake(args: list[str]) -> object:
        calls["n"] += 1
        if calls["n"] == 1:
            return refs
        return {"tag": "v1.0.0", "verification": {"verified": True}}

    monkeypatch.setattr(preflight, "_gh_json", _fake)
    r = preflight.check_tag_verification("o/r")[0]
    assert r.status == preflight.MET
    assert "v1.0.0" in r.reason


def test_check_org_2fa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_json", lambda a: {"two_factor_requirement_enabled": True})
    assert preflight.check_org_2fa("o/r")[0].status == preflight.MET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: {"two_factor_requirement_enabled": False})
    assert preflight.check_org_2fa("o/r")[0].status == preflight.UNMET
    monkeypatch.setattr(preflight, "_gh_json", lambda a: {"two_factor_requirement_enabled": None})
    assert preflight.check_org_2fa("o/r")[0].status == preflight.HUMAN
    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    assert preflight.check_org_2fa("o/r")[0].status == preflight.HUMAN


# --- remote orchestration degrades when gh absent --------------------------


def test_check_remote_no_gh_all_human(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    results = preflight.check_remote("o/r", "bob")
    assert results
    assert all(r.status == preflight.HUMAN for r in results)
    assert any(r.criterion == "require_2FA" for r in results)


def test_check_remote_with_gh_runs_each_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: True)
    monkeypatch.setattr(preflight, "_gh_json", lambda a: None)
    monkeypatch.setattr(preflight, "_gh", lambda a: (127, ""))
    results = preflight.check_remote("o/r", "bob")
    # Seven remote criteria attempted even when each individually degrades
    # (repo_public, branch_protection, scorecard_token_secret, good_first_issue,
    # two_person_review_collaborator, version_tags_signed_verified, require_2FA).
    assert len(results) == 7
    assert any(r.criterion == "scorecard_token_secret" for r in results)


# --- orchestration + main --------------------------------------------------


def test_run_checks_and_report(
    tmp_path: Path, tokens: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path)
    results = preflight.run_checks(repo, "silver", tokens, "acme-v/acme-lib")
    counts = preflight.print_report(results, "silver", "acme-v/acme-lib")
    assert counts[preflight.MET] >= 1
    assert counts[preflight.HUMAN] >= 1
    assert sum(counts.values()) == len(results)


def test_run_checks_scopes_gold_only_criteria(
    tmp_path: Path, tokens: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path)
    silver = {r.criterion for r in preflight.run_checks(repo, "silver", tokens, "acme-v/acme-lib")}
    gold = {r.criterion for r in preflight.run_checks(repo, "gold", tokens, "acme-v/acme-lib")}
    # Gold-only criteria are not reported (as UNMET or anything) at silver.
    assert "per_file_license_spdx" not in silver
    assert "require_2FA" not in silver
    # But they are reported at gold.
    assert "per_file_license_spdx" in gold
    assert "require_2FA" in gold


def test_main_silver_omits_gold_criteria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path)
    rc = preflight.main(["--repo-path", str(repo), "--tier", "silver"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "per_file_license_spdx" not in out
    assert "require_2FA" not in out


def test_main_gold_tier_runs_and_lists_gold_criteria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path)
    rc = preflight.main(["--repo-path", str(repo), "--tier", "gold"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "per_file_license_spdx" in out
    assert "require_2FA" in out


def test_main_reports_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path)
    rc = preflight.main(["--repo-path", str(repo), "--tier", "silver"])
    assert rc == 0
    assert "preflight" in capsys.readouterr().out


def test_main_strict_nonzero_on_unmet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh_available", lambda: False)
    repo = _make_repo(tmp_path, docs=False)  # everything missing → UNMET
    rc = preflight.main(["--repo-path", str(repo), "--tier", "passing", "--strict"])
    assert rc == 1


def test_main_bad_repo_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "nope"
    rc = preflight.main(["--repo-path", str(missing), "--tier", "silver"])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


def test_main_missing_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()  # dir exists but no hardening.toml
    rc = preflight.main(["--repo-path", str(repo), "--tier", "silver"])
    assert rc == 2
    assert "manifest not found" in capsys.readouterr().err


# --- workflow hardening (existing-workflow Token-Permissions + Pinned-Deps) --

_SHA = "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"  # 40-hex, a real checkout SHA


def test_workflow_hardening_all_met(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        "name: CI\npermissions:\n  contents: read\n"
        f"jobs:\n  t:\n    steps:\n      - uses: actions/checkout@{_SHA} # v7\n",
    )
    results = preflight.check_workflow_hardening(tmp_path)
    by = {r.criterion: r for r in results}
    assert by["workflow_token_permissions"].status == preflight.MET
    assert by["workflow_pinned_actions"].status == preflight.MET


def test_workflow_missing_top_level_permissions_is_unmet(tmp_path: Path) -> None:
    # Job-scoped permissions only (indented) must NOT count as top-level.
    _write_workflow(
        tmp_path,
        "codeql.yml",
        "name: CodeQL\njobs:\n  a:\n    permissions:\n      security-events: write\n"
        f"    steps:\n      - uses: actions/checkout@{_SHA} # v7\n",
    )
    by = {r.criterion: r for r in preflight.check_workflow_hardening(tmp_path)}
    assert by["workflow_token_permissions"].status == preflight.UNMET
    assert "codeql.yml" in by["workflow_token_permissions"].reason


def test_workflow_tag_pinned_uses_is_unmet(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        "name: CI\npermissions:\n  contents: read\n"
        "jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n",
    )
    by = {r.criterion: r for r in preflight.check_workflow_hardening(tmp_path)}
    assert by["workflow_pinned_actions"].status == preflight.UNMET
    assert "actions/checkout@v4" in by["workflow_pinned_actions"].reason


def test_workflow_local_and_docker_uses_are_exempt(tmp_path: Path) -> None:
    _write_workflow(
        tmp_path,
        "ci.yml",
        "name: CI\npermissions:\n  contents: read\n"
        "jobs:\n  t:\n    steps:\n"
        "      - uses: ./.github/actions/local\n"
        "      - uses: docker://alpine:3.20\n",
    )
    by = {r.criterion: r for r in preflight.check_workflow_hardening(tmp_path)}
    assert by["workflow_pinned_actions"].status == preflight.MET


def test_workflow_hardening_no_workflows_is_human(tmp_path: Path) -> None:
    (result,) = preflight.check_workflow_hardening(tmp_path)
    assert result.status == preflight.HUMAN


def test_unpinned_uses_helper() -> None:
    text = (
        f"      - uses: actions/checkout@{_SHA}\n"
        "      - uses: actions/setup-python@v6\n"
        "      - uses: ./local\n"
    )
    assert preflight._unpinned_uses(text) == ["actions/setup-python@v6"]


def test_scorecard_token_secret_states(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(preflight, "_gh", lambda args: (0, ""))
    assert preflight.check_scorecard_token("o/r")[0].status == preflight.MET
    monkeypatch.setattr(preflight, "_gh", lambda args: (1, ""))
    assert preflight.check_scorecard_token("o/r")[0].status == preflight.UNMET
    monkeypatch.setattr(preflight, "_gh", lambda args: (127, ""))
    assert preflight.check_scorecard_token("o/r")[0].status == preflight.HUMAN
