# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Template guarantees: no x402 domain leakage, and every template renders clean.

These two tests are the enforcement mechanism behind the skill's promise that
project-specific content never rides along into a target repo, and that a fully
edited manifest always produces token-complete output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render  # noqa: E402

TEMPLATES = ROOT / "templates"

# Unambiguous x402-domain terms. A generalized template must never contain these;
# the real x402 artifacts live under docs/examples/x402/ (a worked example), which
# is deliberately NOT scanned.
FORBIDDEN = [
    "x402",
    "presidio_x402",
    "screening",
    "facilitator",
    "mainnet",
    "coinbase",
    "spacy",
    "replay fingerprint",
]


def _template_files() -> list[Path]:
    return sorted(p for p in TEMPLATES.rglob("*") if p.is_file())


def test_templates_exist() -> None:
    assert _template_files(), "no templates found — build has not run"


@pytest.mark.parametrize("term", FORBIDDEN)
def test_no_x402_domain_leakage(term: str) -> None:
    hits = []
    for path in _template_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if term in text:
            hits.append(str(path.relative_to(ROOT)))
    assert not hits, f"x402 domain term {term!r} leaked into templates: {hits}"


def test_every_template_renders_clean() -> None:
    """The skill's own manifest must render every template with no unresolved token."""
    tokens = render.load_manifest(ROOT / "hardening.toml")
    failures = []
    for path in _template_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            rendered = render.render_text(text, tokens)
        except render.RenderError as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        # No {{...}} may survive a successful render.
        leftover = render.TOKEN_RE.findall(rendered)
        if leftover:
            failures.append(f"{path.relative_to(ROOT)}: unresolved {sorted(set(leftover))}")
    assert not failures, "templates failed to render:\n" + "\n".join(failures)
