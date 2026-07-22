# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""SPDX-header insert/verify contract tests.

Covers header insertion after a shebang, idempotency, ``--check`` exit codes,
the skip list, the ``.py`` vs ``.sh`` comment styles, and manifest-driven
holder/license selection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import spdx_headers  # noqa: E402

MANIFEST = """\
[project]
name = "acme-lib"
org = "acme-v"

[legal]
copyright_holder = "Acme Inc"
license = "MIT"
"""


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    m = tmp_path / "hardening.toml"
    m.write_text(MANIFEST, encoding="utf-8")
    return m


# --- pure helpers ----------------------------------------------------------


def test_comment_leader_by_suffix() -> None:
    assert spdx_headers.comment_leader(Path("a.py")) == "#"
    assert spdx_headers.comment_leader(Path("a.sh")) == "#"
    assert spdx_headers.comment_leader(Path("a.md")) is None
    assert spdx_headers.comment_leader(Path("a.rs")) is None


def test_is_skipped() -> None:
    assert spdx_headers.is_skipped(Path("proj/.venv/lib/x.py"))
    assert spdx_headers.is_skipped(Path("proj/__pycache__/x.py"))
    assert spdx_headers.is_skipped(Path("dist/x.py"))
    assert not spdx_headers.is_skipped(Path("proj/src/x.py"))


def test_has_spdx_header() -> None:
    assert spdx_headers.has_spdx_header("# SPDX-License-Identifier: MIT\ncode")
    assert not spdx_headers.has_spdx_header("just code\n")


def test_build_header() -> None:
    header = spdx_headers.build_header("#", "MIT", "2026", "Acme Inc")
    assert header == "# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 Acme Inc"


def test_insert_header_no_shebang() -> None:
    out = spdx_headers.insert_header("import os\n", "# HDR")
    assert out == "# HDR\nimport os\n"


def test_insert_header_after_shebang() -> None:
    out = spdx_headers.insert_header("#!/usr/bin/env python3\nimport os\n", "# HDR")
    assert out == "#!/usr/bin/env python3\n# HDR\nimport os\n"
    # The shebang must remain line one so the file stays executable.
    assert out.startswith("#!")


# --- file discovery --------------------------------------------------------


def test_iter_source_files_filters_and_skips(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "keep.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "script.sh").write_text("echo hi\n", encoding="utf-8")
    (tmp_path / "src" / "notes.md").write_text("# doc\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "vendored.py").write_text("x = 1\n", encoding="utf-8")

    found = spdx_headers.iter_source_files([str(tmp_path)])
    names = sorted(p.name for p in found)
    assert names == ["keep.py", "script.sh"]  # .md dropped, .venv skipped


def test_iter_source_files_accepts_a_file_path(tmp_path: Path) -> None:
    f = tmp_path / "one.py"
    f.write_text("x = 1\n", encoding="utf-8")
    found = spdx_headers.iter_source_files([str(f)])
    assert found == [f]


# --- check mode ------------------------------------------------------------


def test_cmd_check_flags_missing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "good.py"
    good.write_text("# SPDX-License-Identifier: MIT\nx = 1\n", encoding="utf-8")
    bad = tmp_path / "bad.py"
    bad.write_text("x = 1\n", encoding="utf-8")

    rc = spdx_headers.cmd_check([good, bad])
    assert rc == 1
    out = capsys.readouterr().out
    assert "MISSING SPDX HEADER" in out
    assert "bad.py" in out


def test_cmd_check_all_covered(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = tmp_path / "good.py"
    good.write_text("# SPDX-License-Identifier: MIT\nx = 1\n", encoding="utf-8")
    rc = spdx_headers.cmd_check([good])
    assert rc == 0
    assert "clean" in capsys.readouterr().out


# --- apply mode + idempotency ---------------------------------------------


def test_cmd_apply_inserts_and_reads_manifest(manifest: Path, tmp_path: Path) -> None:
    from render import load_manifest

    tokens = load_manifest(manifest)
    py = tmp_path / "mod.py"
    py.write_text("import os\n", encoding="utf-8")
    sh = tmp_path / "run.sh"
    sh.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")

    rc = spdx_headers.cmd_apply([py, sh], tokens)
    assert rc == 0

    py_text = py.read_text(encoding="utf-8")
    assert py_text.startswith("# SPDX-License-Identifier: MIT\n# Copyright (c) ")
    assert "Acme Inc" in py_text
    assert py_text.endswith("import os\n")

    # Shebang stays on line one for the .sh file, header inserted after it.
    sh_lines = sh.read_text(encoding="utf-8").splitlines()
    assert sh_lines[0] == "#!/bin/sh"
    assert sh_lines[1] == "# SPDX-License-Identifier: MIT"


def test_cmd_apply_is_idempotent(manifest: Path, tmp_path: Path) -> None:
    from render import load_manifest

    tokens = load_manifest(manifest)
    py = tmp_path / "mod.py"
    py.write_text("import os\n", encoding="utf-8")

    spdx_headers.cmd_apply([py], tokens)
    first = py.read_text(encoding="utf-8")
    spdx_headers.cmd_apply([py], tokens)
    second = py.read_text(encoding="utf-8")
    assert first == second  # second pass changes nothing


# --- main() dispatch -------------------------------------------------------


def test_main_check_returns_nonzero(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("x = 1\n", encoding="utf-8")
    assert spdx_headers.main(["--check", str(bad)]) == 1


def test_main_apply_then_check_clean(manifest: Path, tmp_path: Path) -> None:
    py = tmp_path / "mod.py"
    py.write_text("x = 1\n", encoding="utf-8")
    assert spdx_headers.main(["--apply", "--manifest", str(manifest), str(py)]) == 0
    assert spdx_headers.main(["--check", str(py)]) == 0


def test_main_no_supported_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "readme.md").write_text("# doc\n", encoding="utf-8")
    rc = spdx_headers.main(["--check", str(tmp_path)])
    assert rc == 0
    assert "no supported source files found" in capsys.readouterr().err
