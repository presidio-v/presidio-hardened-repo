# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Atheris coverage-guided fuzz harness for the strict template renderer.

The renderer's two regex parsers (`render_text` token substitution and
`find_fill_markers`) run over arbitrary template text supplied by whoever authors
a target repo's templates — untrusted-ish input worth fuzzing for pathological
regex behaviour or crashes.

GOTCHAS (read before running):
  - No macOS Atheris wheel: run under Linux CI only, never on a developer Mac.
  - No cp310/cp311 Atheris wheel: run under Python 3.12.
  - Editable installs can shadow modules on sys.path; make sure `render` resolves
    to this repo's scripts/render.py (it does, via the path insert below).
"""

import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
with atheris.instrument_imports():
    import render

# A fixed token map so render_text has something to resolve; unknown tokens in
# the fuzzed text raise RenderError, which is the renderer's expected contract.
_TOKENS = {
    "PROJECT_NAME": "acme-lib",
    "PROJECT_ORG": "acme-v",
    "YEAR": "2026",
    "REPO_SLUG": "acme-v/acme-lib",
}


def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())
    try:
        render.render_text(text, _TOKENS)
    except render.RenderError:
        # Expected: the fuzzed text referenced a token not in _TOKENS.
        pass
    render.find_fill_markers(text)


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
