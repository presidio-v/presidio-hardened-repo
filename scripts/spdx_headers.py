# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Insert and verify SPDX + copyright headers on source files.

Supports the OpenSSF gold criteria ``copyright_per_file`` and
``license_per_file``: every source file carries a two-line header naming its
license (as an SPDX identifier) and copyright holder. This script is the
mechanical half — a CI ``--check`` gate that fails when a file is missing the
header, and an ``--apply`` pass that inserts it.

The holder and license come from the target's ``hardening.toml`` manifest
(``LEGAL_COPYRIGHT_HOLDER``, ``LEGAL_LICENSE``); the year is the current UTC
year. The header for a ``.py`` file is::

    # SPDX-License-Identifier: <license>
    # Copyright (c) <year> <holder>

It is placed after an optional shebang line and before all other content.
``--apply`` is idempotent: a file that already has an ``SPDX-License-Identifier``
line is left untouched.

stdlib only, Python 3.11+ (``tomllib``). Reuses ``render.load_manifest``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from render import load_manifest

# Comment leader per file extension. Python-first; extend as needed.
COMMENT_STYLES: dict[str, str] = {
    ".py": "#",
    ".sh": "#",
}

# Path fragments whose files are never headed (vendored / generated / build).
SKIP_DIRS = frozenset({".venv", "venv", "dist", "build", "__pycache__", "migrations", ".git"})

SPDX_TAG = "SPDX-License-Identifier"


def is_skipped(path: Path) -> bool:
    """True if any path component is in the skip list."""
    return any(part in SKIP_DIRS for part in path.parts)


def comment_leader(path: Path) -> str | None:
    """Return the comment leader for a file, or None if unsupported."""
    return COMMENT_STYLES.get(path.suffix)


def has_spdx_header(text: str) -> bool:
    """True if the text already carries an SPDX-License-Identifier line."""
    return SPDX_TAG in text


def build_header(leader: str, license_id: str, year: str, holder: str) -> str:
    """Build the two-line header block (no trailing newline)."""
    return f"{leader} {SPDX_TAG}: {license_id}\n{leader} Copyright (c) {year} {holder}"


def insert_header(text: str, header: str) -> str:
    """Insert the header after an optional shebang, before other content."""
    if text.startswith("#!"):
        shebang, _, rest = text.partition("\n")
        return f"{shebang}\n{header}\n{rest}"
    return f"{header}\n{text}"


def iter_source_files(paths: list[str]) -> list[Path]:
    """Expand CLI paths into supported, non-skipped source files."""
    found: list[Path] = []
    for raw in paths:
        root = Path(raw)
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            if path.is_file() and comment_leader(path) and not is_skipped(path):
                found.append(path)
    return found


def cmd_check(files: list[Path]) -> int:
    """Exit 1 and list files missing a header; exit 0 if all covered."""
    missing = [p for p in files if not has_spdx_header(p.read_text(encoding="utf-8"))]
    for path in missing:
        print(f"MISSING SPDX HEADER {path}")
    if missing:
        print(f"\n{len(missing)} file(s) missing a header.", file=sys.stderr)
        return 1
    print(f"clean: {len(files)} file(s) carry an SPDX header")
    return 0


def cmd_apply(files: list[Path], tokens: dict[str, str]) -> int:
    """Insert a header into files that lack one; report count changed."""
    license_id = tokens["LEGAL_LICENSE"]
    holder = tokens["LEGAL_COPYRIGHT_HOLDER"]
    year = tokens["YEAR"]
    changed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        if has_spdx_header(text):
            continue
        leader = comment_leader(path)
        assert leader is not None  # iter_source_files guarantees this
        header = build_header(leader, license_id, year, holder)
        path.write_text(insert_header(text, header), encoding="utf-8")
        changed += 1
    print(f"applied header to {changed} file(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Insert/verify SPDX + copyright headers.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if any file lacks a header")
    mode.add_argument("--apply", action="store_true", help="insert missing headers")
    parser.add_argument("--manifest", default="hardening.toml", help="path to hardening.toml")
    parser.add_argument("paths", nargs="+", help="files or directories to scan")
    args = parser.parse_args(argv)

    files = iter_source_files(args.paths)
    if not files:
        print("no supported source files found", file=sys.stderr)
        return 0

    if args.check:
        return cmd_check(files)
    tokens = load_manifest(Path(args.manifest))
    return cmd_apply(files, tokens)


if __name__ == "__main__":
    raise SystemExit(main())
