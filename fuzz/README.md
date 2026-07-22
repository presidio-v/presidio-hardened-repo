# Fuzzing

Coverage-guided fuzzing of presidio-hardened-repo with Atheris.

    python -m pip install '.[fuzz]'
    python fuzz_render.py             # runs until a crash or Ctrl-C

`fuzz_render.py` drives the renderer's two regex parsers (`render_text`,
`find_fill_markers`) over arbitrary input.

Gotchas: no macOS Atheris wheel (Linux CI only); no cp310 wheel, so run under
Python 3.12; an editable install can shadow the installed package, so fuzz the
built wheel. The harness MUST import and drive the real target module — that is
what makes OpenSSF Scorecard's literal `import atheris` detection and its
dynamic_analysis check both hold.
