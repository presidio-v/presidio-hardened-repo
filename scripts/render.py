# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Strict template renderer for presidio-hardened-repo.

Turns a per-target ``hardening.toml`` manifest into concrete repository files by
substituting ``{{TOKEN}}`` placeholders in the ``templates/`` tree.

Design contract (the reason this is a script and not prose):

* **Fail hard on unresolved tokens.** A ``{{TOKEN}}`` with no manifest value is
  an error, not a silently empty string. A template that references a token the
  manifest does not define is also an error. This is what stops a half-rendered
  governance doc from ever reaching a target repo.
* **FILL markers are judgment work, not rendering.** ``<!-- FILL:slug -->`` (and
  the ``# FILL:slug`` form) mark places where Claude must write prose after
  reading the *target* codebase — a threat model, a trust-boundary table. The
  renderer never fills them; ``--check`` reports any that survive so a phase is
  not declared complete while judgment work is outstanding.
* **stdlib only.** No jinja, no external deps — the skill hardens repos, it must
  not drag a dependency graph into them. Requires Python 3.11+ (``tomllib``).

Tokens are the manifest flattened as ``SECTION_KEY`` uppercased, e.g.
``[project] name = "x"`` -> ``{{PROJECT_NAME}}``. Two computed tokens are always
available: ``{{YEAR}}`` (current UTC year) and ``{{REPO_SLUG}}``
(``org/name``).
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
import tomllib
from pathlib import Path

TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
FILL_RE = re.compile(r"(?:<!--|#)\s*FILL:([a-z0-9\-]+)\s*(?:-->)?")


class RenderError(Exception):
    """Raised on any unresolved or undefined token — never swallowed."""


def load_manifest(path: Path) -> dict[str, str]:
    """Flatten ``hardening.toml`` into an uppercase ``SECTION_KEY`` token map."""
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    tokens: dict[str, str] = {}
    for section, body in data.items():
        if not isinstance(body, dict):
            # Top-level scalars are allowed but discouraged; expose bare.
            tokens[section.upper()] = _stringify(body)
            continue
        for key, value in body.items():
            tokens[f"{section.upper()}_{key.upper()}"] = _stringify(value)

    # Computed tokens.
    tokens["YEAR"] = str(datetime.datetime.now(tz=datetime.UTC).year)
    org = tokens.get("PROJECT_ORG", "")
    name = tokens.get("PROJECT_NAME", "")
    if org and name:
        tokens["REPO_SLUG"] = f"{org}/{name}"
    return tokens


def _stringify(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def render_text(text: str, tokens: dict[str, str]) -> str:
    """Substitute every ``{{TOKEN}}``; raise on any the manifest cannot resolve."""
    missing: set[str] = set()

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in tokens:
            missing.add(name)
            return match.group(0)
        return tokens[name]

    result = TOKEN_RE.sub(_sub, text)
    if missing:
        raise RenderError(
            "template references tokens absent from the manifest: " + ", ".join(sorted(missing))
        )
    return result


def find_fill_markers(text: str) -> list[str]:
    """Return the slugs of any surviving ``FILL:`` judgment markers."""
    return [m.group(1) for m in FILL_RE.finditer(text)]


def render_file(src: Path, dst: Path, tokens: dict[str, str]) -> list[str]:
    """Render one template to ``dst``; return surviving FILL slugs (never fills)."""
    text = src.read_text(encoding="utf-8")
    rendered = render_text(text, tokens)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(rendered, encoding="utf-8")
    return find_fill_markers(rendered)


def _dst_name(src: Path) -> str:
    """Strip a single trailing ``.tmpl`` suffix; other names pass through."""
    return src.name[: -len(".tmpl")] if src.suffix == ".tmpl" else src.name


def cmd_render(args: argparse.Namespace) -> int:
    tokens = load_manifest(Path(args.manifest))
    src_root = Path(args.templates)
    out_root = Path(args.out)
    sources = sorted(p for p in src_root.rglob("*") if p.is_file())
    if not sources:
        print(f"no templates under {src_root}", file=sys.stderr)
        return 1

    pending: dict[str, list[str]] = {}
    for src in sources:
        rel = src.relative_to(src_root).with_name(_dst_name(src))
        dst = out_root / rel
        try:
            fills = render_file(src, dst, tokens)
        except RenderError as exc:
            print(f"ERROR {src}: {exc}", file=sys.stderr)
            return 2
        if fills:
            pending[str(rel)] = fills
        print(f"rendered {rel}")

    if pending:
        print("\nFILL markers awaiting judgment work (Claude must resolve):")
        for rel, slugs in pending.items():
            print(f"  {rel}: {', '.join(slugs)}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Report unresolved tokens and surviving FILL markers under a path."""
    root = Path(args.path)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    problems = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        tokens = TOKEN_RE.findall(text)
        fills = find_fill_markers(text)
        if tokens:
            print(f"UNRESOLVED TOKENS {path}: {', '.join(sorted(set(tokens)))}")
            problems += 1
        if fills:
            print(f"OPEN FILL MARKERS {path}: {', '.join(fills)}")
            problems += 1
    if problems:
        print(f"\n{problems} file(s) not ready.", file=sys.stderr)
        return 1
    print("clean: no unresolved tokens, no open FILL markers")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Strict template renderer.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render a templates tree to an output root")
    p_render.add_argument("--manifest", required=True)
    p_render.add_argument("--templates", required=True)
    p_render.add_argument("--out", required=True)
    p_render.set_defaults(func=cmd_render)

    p_check = sub.add_parser("check", help="scan for unresolved tokens / open FILL markers")
    p_check.add_argument("path")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
