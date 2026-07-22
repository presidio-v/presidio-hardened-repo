# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Renderer contract tests — the strict-token guarantee must not regress."""

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
package = "acme_lib"
description = "A thing."
language = "python"
tier = "silver"

[people]
maintainer = "alice"
reviewer = "bob"
security_contact = "security@acme.example"

[legal]
copyright_holder = "Acme Inc"
license = "MIT"

[badge]
bestpractices_id = 42
"""


@pytest.fixture
def tokens(tmp_path: Path) -> dict[str, str]:
    m = tmp_path / "hardening.toml"
    m.write_text(MANIFEST, encoding="utf-8")
    return render.load_manifest(m)


def test_flatten_and_computed_tokens(tokens: dict[str, str]) -> None:
    assert tokens["PROJECT_NAME"] == "acme-lib"
    assert tokens["PEOPLE_REVIEWER"] == "bob"
    assert tokens["LEGAL_COPYRIGHT_HOLDER"] == "Acme Inc"
    assert tokens["BADGE_BESTPRACTICES_ID"] == "42"
    assert tokens["REPO_SLUG"] == "acme-v/acme-lib"
    assert tokens["YEAR"].isdigit() and len(tokens["YEAR"]) == 4


def test_substitution(tokens: dict[str, str]) -> None:
    out = render.render_text("owned by {{LEGAL_COPYRIGHT_HOLDER}} ({{REPO_SLUG}})", tokens)
    assert out == "owned by Acme Inc (acme-v/acme-lib)"


def test_unresolved_token_raises(tokens: dict[str, str]) -> None:
    with pytest.raises(render.RenderError, match="NONEXISTENT_TOKEN"):
        render.render_text("hello {{NONEXISTENT_TOKEN}}", tokens)


def test_fill_markers_detected() -> None:
    html = "<!-- FILL:threat-model --> and # FILL:trust-boundaries"
    assert render.find_fill_markers(html) == ["threat-model", "trust-boundaries"]


def test_no_fill_markers_when_clean() -> None:
    assert render.find_fill_markers("nothing to fill here") == []


def test_render_file_strips_tmpl_suffix(tmp_path: Path, tokens: dict[str, str]) -> None:
    src = tmp_path / "CODEOWNERS.tmpl"
    src.write_text("* @{{PEOPLE_MAINTAINER}} @{{PEOPLE_REVIEWER}}\n", encoding="utf-8")
    dst = tmp_path / "out" / render._dst_name(src)
    fills = render.render_file(src, dst, tokens)
    assert dst.name == "CODEOWNERS"
    assert dst.read_text(encoding="utf-8") == "* @alice @bob\n"
    assert fills == []


def test_check_reports_open_fill(tmp_path: Path) -> None:
    f = tmp_path / "ARCHITECTURE.md"
    f.write_text("# Arch\n<!-- FILL:components -->\n", encoding="utf-8")
    rc = render.main(["check", str(f)])
    assert rc == 1


def test_check_clean(tmp_path: Path) -> None:
    f = tmp_path / "GOVERNANCE.md"
    f.write_text("# Governance\nAll good.\n", encoding="utf-8")
    rc = render.main(["check", str(f)])
    assert rc == 0
