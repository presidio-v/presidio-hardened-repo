# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""CLI-level tests for the renderer: cmd_render, cmd_check, main() dispatch.

The contract these exercise: a templates tree renders to an out dir with
``.tmpl`` suffixes stripped, FILL markers are reported (never filled), an
undefined token aborts with exit 2, and check reports clean vs dirty paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import render  # noqa: E402

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
"""


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    m = tmp_path / "hardening.toml"
    m.write_text(MANIFEST, encoding="utf-8")
    return m


def _templates(root: Path) -> Path:
    tpl = root / "templates"
    (tpl / "sub").mkdir(parents=True)
    (tpl / "CODEOWNERS.tmpl").write_text("* @{{PEOPLE_MAINTAINER}}\n", encoding="utf-8")
    (tpl / "sub" / "ARCH.md").write_text(
        "# {{PROJECT_NAME}}\n<!-- FILL:threat-model -->\n", encoding="utf-8"
    )
    return tpl


def test_cmd_render_writes_tree_and_reports_fill(
    manifest: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tpl = _templates(tmp_path)
    out = tmp_path / "out"
    rc = render.main(
        ["render", "--manifest", str(manifest), "--templates", str(tpl), "--out", str(out)]
    )
    assert rc == 0

    # .tmpl suffix stripped, token substituted.
    assert (out / "CODEOWNERS").read_text(encoding="utf-8") == "* @alice\n"
    # Nested file rendered, its FILL marker preserved (never filled).
    arch = (out / "sub" / "ARCH.md").read_text(encoding="utf-8")
    assert arch == "# acme-lib\n<!-- FILL:threat-model -->\n"

    stdout = capsys.readouterr().out
    assert "rendered CODEOWNERS" in stdout
    assert "FILL markers awaiting judgment work" in stdout
    assert "threat-model" in stdout


def test_cmd_render_empty_tree_returns_1(
    manifest: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    out = tmp_path / "out"
    rc = render.main(
        ["render", "--manifest", str(manifest), "--templates", str(empty), "--out", str(out)]
    )
    assert rc == 1
    assert "no templates under" in capsys.readouterr().err


def test_cmd_render_undefined_token_exits_2(
    manifest: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tpl = tmp_path / "templates"
    tpl.mkdir()
    (tpl / "BAD.md").write_text("uses {{NOPE_TOKEN}}\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = render.main(
        ["render", "--manifest", str(manifest), "--templates", str(tpl), "--out", str(out)]
    )
    assert rc == 2
    assert "ERROR" in capsys.readouterr().err
    assert not (out / "BAD.md").exists()  # nothing written on failure


def test_cmd_check_dir_with_unresolved_token(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    d = tmp_path / "tree"
    d.mkdir()
    (d / "leftover.md").write_text("still has {{PROJECT_NAME}}\n", encoding="utf-8")
    rc = render.main(["check", str(d)])
    assert rc == 1
    assert "UNRESOLVED TOKENS" in capsys.readouterr().out


def test_cmd_check_dir_clean(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    d = tmp_path / "tree"
    d.mkdir()
    (d / "ok.md").write_text("all resolved, nothing to fill\n", encoding="utf-8")
    rc = render.main(["check", str(d)])
    assert rc == 0
    assert "clean" in capsys.readouterr().out


def test_cmd_check_skips_binary(tmp_path: Path) -> None:
    d = tmp_path / "tree"
    d.mkdir()
    (d / "blob.bin").write_bytes(b"\xff\xfe\x00\x01not utf8")
    (d / "ok.md").write_text("fine\n", encoding="utf-8")
    # Undecodable file is skipped, not fatal.
    assert render.main(["check", str(d)]) == 0


def test_main_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        render.main([])
