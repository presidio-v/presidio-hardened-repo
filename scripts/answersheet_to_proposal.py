# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Turn a filled OpenSSF answer sheet into a bestpractices.dev proposal URL.

The OpenSSF BadgeApp supports *automation proposals*
(``ossf/best-practices-badge`` ``docs/automation-proposals.md``): a tool encodes
suggested criterion values as query parameters on a project's edit URL, and the
**authorized human** opens that URL, reviews each highlighted proposal, and
accepts or ignores it. The tool only *proposes* — it never writes to the
BadgeApp, and the human remains the final arbiter of every attestation. This
matches the skill's one overriding rule: never over-claim, never fabricate.

Given a filled answer-sheet markdown file (``plan/cii-passing-answers.md``,
``plan/cii-silver-answers.md`` …) shaped as ``| Criterion | Status |
Justification |`` tables, this script produces one or more click-to-propose
URLs of the form::

    https://www.bestpractices.dev/projects/<id>/choose/edit?<crit>_status=Met&<crit>_justification=...

Proposals are *unforced* by default: the BadgeApp only fills a field that is
currently blank. Pass ``--overrides '*'`` (or a comma-separated glob list) to let
the proposals overwrite fields that already have a value — the human still
reviews each one.

The script does no network and no subprocess work: it parses a local file and
prints URLs. Requires Python 3.11+ (for ``render.load_manifest`` / ``tomllib``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render  # noqa: E402

BASE = "https://www.bestpractices.dev/projects/{id}/{section}/edit?"


def infer_section(sheet_path: Path) -> str:
    """Derive the badge-level section (passing|silver|gold) from the sheet filename.

    bestpractices.dev silently ignores a field that does not belong to the section
    named in the URL, so the section MUST match the sheet's tier — `choose` does not
    carry level criteria and leaves the form empty (the original bug).
    """
    name = sheet_path.name.lower()
    for tier in ("passing", "silver", "gold"):
        if tier in name:
            return tier
    return "choose"


# The sheets abbreviate the repo URL as a bare ``REPO`` shorthand in
# justifications (``REPO/blob/main/LICENSE``, ``REPO#readme``, ``REPO/issues``),
# defined once at the top as ``REPO = https://github.com/<slug>``. ``render.py``
# only expands ``{{TOKEN}}`` placeholders, so this shorthand survives into the
# rendered sheet — and a proposal that carried a literal ``REPO/...`` string
# would be an unusable justification. Expand it here against the manifest slug.
# ``\bREPO\b`` matches the standalone token and the ``REPO/``, ``REPO#`` forms
# (``/`` and ``#`` are word boundaries) without touching ``REPORT`` or ``REPO_``.
_REPO_SHORTHAND_RE = re.compile(r"\bREPO\b")

# A normalized criterion is a lowercase identifier: letters, digits, underscore.
_CRITERION_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# First backtick-delimited token in a Criterion cell, e.g. `bus_factor` (SHOULD).
_BACKTICK_RE = re.compile(r"`([^`]+)`")
# Markdown-table separator cell: ---, :---, ---:, :---:
_SEPARATOR_RE = re.compile(r"^:?-+:?$")
# Header words that appear in a status column and are not real statuses.
_HEADER_STATUS = {"status", "answer"}


class ProposalError(Exception):
    """Raised on an unusable project id or an otherwise unbuildable URL."""


def strip_markdown(text: str) -> str:
    """Remove bold markers and backticks; collapse surrounding whitespace."""
    return text.replace("**", "").replace("`", "").strip()


def normalize_criterion(cell: str) -> str | None:
    """Extract and normalize a criterion name, or ``None`` if the cell is not one.

    The Criterion cell usually wraps the name in backticks (``\\`description_good\\```)
    and may carry a trailing note (``\\`bus_factor\\` (SHOULD)``). We take the first
    backtick token when present, otherwise the first whitespace token, lowercase
    it, map ``.``/``-`` to ``_``, and require a bare identifier.
    """
    match = _BACKTICK_RE.search(cell)
    if match:
        raw = match.group(1)
    else:
        # No backticks: a real criterion cell is a single bare token. Multi-word
        # cells (e.g. a section header "Basics — documentation") are not criteria.
        raw = cell.replace("*", "")
        if len(raw.split()) != 1:
            return None
    tokens = raw.split()
    if not tokens:
        return None
    name = tokens[0].strip().lower().replace(".", "_").replace("-", "_")
    return name if _CRITERION_RE.fullmatch(name) else None


def normalize_status(cell: str) -> str:
    """Map a status cell to one of ``Met`` / ``Unmet`` / ``N/A`` / ``?``.

    Order matters: ``N/A`` and ``Unmet`` both must be tested before ``Met``
    because the substring ``met`` also appears inside ``unmet``.
    """
    text = strip_markdown(cell).lower()
    if not text or text == "?" or "unknown" in text:
        return "?"
    if "n/a" in text or "n-a" in text:
        return "N/A"
    if "unmet" in text or "pending" in text:
        return "Unmet"
    if "met" in text:
        return "Met"
    return "?"


def _split_row(line: str) -> list[str] | None:
    """Split a markdown table line into cells, or ``None`` if it is not a row."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    body = stripped[1:]
    if body.endswith("|"):
        body = body[:-1]
    # Split on unescaped pipes only, then restore the escaped ones.
    cells = re.split(r"(?<!\\)\|", body)
    return [cell.replace("\\|", "|").strip() for cell in cells]


def _is_separator(cells: list[str]) -> bool:
    return all(_SEPARATOR_RE.fullmatch(c.strip()) for c in cells if c.strip())


def parse_sheet(text: str) -> list[tuple[str, str, str]]:
    """Parse answer-sheet markdown into ``(criterion, status, justification)`` rows.

    Skips separator rows, header rows, and any row whose first cell is not a
    recognizable criterion name (section headers, prose). Order is preserved.
    """
    rows: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        cells = _split_row(line)
        if cells is None or len(cells) < 2:
            continue
        if _is_separator(cells):
            continue
        # Skip the "| Criterion | Status | ... |" header row.
        if strip_markdown(cells[1]).lower() in _HEADER_STATUS:
            continue
        criterion = normalize_criterion(cells[0])
        if criterion is None:
            continue
        status = normalize_status(cells[1])
        justification = cells[2].strip() if len(cells) > 2 else ""
        rows.append((criterion, status, justification))
    return rows


def expand_repo_shorthand(text: str, repo_url: str) -> str:
    """Replace the bare ``REPO`` shorthand with the target repo URL.

    ``repo_url`` is ``https://github.com/<slug>`` (no trailing slash). Leaves the
    text untouched when ``repo_url`` is empty so expansion is always best-effort.
    """
    if not repo_url:
        return text
    return _REPO_SHORTHAND_RE.sub(repo_url.rstrip("/"), text)


def expand_rows(rows: list[tuple[str, str, str]], repo_url: str) -> list[tuple[str, str, str]]:
    """Expand the ``REPO`` shorthand in every justification cell."""
    return [(c, s, expand_repo_shorthand(j, repo_url)) for c, s, j in rows]


def repo_url_from_manifest(args: argparse.Namespace) -> str:
    """Return ``https://github.com/<slug>`` from the manifest, or ``""`` if absent.

    Best-effort and never raises: the manifest may be missing (e.g. JSON mode run
    outside a checkout). REPO_SLUG is the same token the sheets render from, so an
    expanded justification matches the URL the human registered.
    """
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = Path(args.repo_path) / manifest_path
    if not manifest_path.is_file():
        return ""
    try:
        tokens = render.load_manifest(manifest_path)
    except Exception:  # noqa: BLE001 — manifest problems must not break proposals
        return ""
    slug = tokens.get("REPO_SLUG", "").strip().strip("/")
    return f"https://github.com/{slug}" if slug else ""


def _criterion_params(criterion: str, status: str, justification: str) -> str:
    """Build the ``&``-joinable query fragment for one criterion (no leading ``&``)."""
    parts = [f"{criterion}_status={quote_plus(status)}"]
    if justification:
        parts.append(f"{criterion}_justification={quote_plus(justification)}")
    return "&".join(parts)


def build_urls(
    project_id: int,
    rows: list[tuple[str, str, str]],
    max_url_len: int = 7000,
    overrides: str | None = None,
    section: str = "choose",
) -> list[str]:
    """Build one or more standalone proposal URLs, chunked to ``max_url_len``.

    Every criterion is emitted; if the full query would exceed ``max_url_len`` the
    criteria are packed greedily across multiple URLs, each a valid standalone
    proposal (each carries the ``overrides`` param when one is set). A single
    criterion whose fragment alone exceeds the cap still gets its own URL rather
    than being dropped.

    ``max_url_len`` defaults to 7000: comfortably under the bestpractices.dev
    server's ~8 KB URI cap (a single 16 KB URL is rejected 414 "URI Too Long"),
    while leaving headroom so no chunk trips the cap.
    """
    if not rows:
        raise ProposalError("no criteria parsed from the sheet — nothing to propose")

    base = BASE.format(id=project_id, section=section)
    prefix = f"overrides={quote_plus(overrides)}" if overrides else ""
    fragments = [_criterion_params(c, s, j) for c, s, j in rows]

    urls: list[str] = []
    current: list[str] = []

    def _flush() -> None:
        if not current:
            return
        parts = ([prefix] if prefix else []) + current
        urls.append(base + "&".join(parts))
        current.clear()

    def _length(candidate: list[str]) -> int:
        parts = ([prefix] if prefix else []) + candidate
        return len(base) + len("&".join(parts))

    for fragment in fragments:
        if current and _length([*current, fragment]) > max_url_len:
            _flush()
        current.append(fragment)
    _flush()
    return urls


def build_bestpractices_mapping(rows: list[tuple[str, str, str]]) -> dict[str, str]:
    """Build the ``.bestpractices.json`` mapping the BadgeApp reads from a repo.

    The OpenSSF BadgeApp seeds proposed answers directly from a
    ``.bestpractices.json`` file committed to a repo's root
    (``ossf/best-practices-badge`` ``docs/bestpractices-json.md``). This sidesteps
    the edit-URL length cap and the multi-URL clobber problem entirely: one file
    carries every criterion. The object is keyed by ``<crit>_status`` and
    ``<crit>_justification`` — the same field names as the URL params, but the
    justifications are stored as plain JSON strings (NOT url-encoded).
    """
    if not rows:
        raise ProposalError("no criteria parsed from the sheet — nothing to propose")
    mapping: dict[str, str] = {}
    for criterion, status, justification in rows:
        mapping[f"{criterion}_status"] = status
        if justification:
            mapping[f"{criterion}_justification"] = justification
    return mapping


def resolve_project_id(args: argparse.Namespace) -> int:
    """Return the numeric project id from ``--id`` or the manifest; error if unusable."""
    if args.id is not None:
        project_id = args.id
    else:
        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = Path(args.repo_path) / manifest_path
        if not manifest_path.is_file():
            raise ProposalError(
                f"manifest not found at {manifest_path} — pass --id N or --manifest PATH"
            )
        tokens = render.load_manifest(manifest_path)
        raw = tokens.get("BADGE_BESTPRACTICES_ID", "0").strip()
        try:
            project_id = int(raw)
        except ValueError as exc:
            raise ProposalError(
                f"badge.bestpractices_id in the manifest is not an integer: {raw!r}"
            ) from exc
    if project_id <= 0:
        raise ProposalError(
            "no bestpractices.dev project id — register the project at "
            "https://www.bestpractices.dev first, then set badge.bestpractices_id "
            "in hardening.toml (or pass --id N)."
        )
    return project_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a filled OpenSSF answer sheet into a bestpractices.dev "
        "automation-proposal URL (the human reviews/accepts each proposal)."
    )
    parser.add_argument("--sheet", required=True, help="filled answer-sheet markdown file")
    parser.add_argument("--repo-path", default=".", help="target repo root (for the manifest)")
    parser.add_argument("--manifest", default="hardening.toml", help="manifest file (id source)")
    parser.add_argument("--id", type=int, default=None, help="project id override")
    parser.add_argument("--max-url-len", type=int, default=7000, help="split URLs above this")
    parser.add_argument(
        "--bestpractices-json",
        default=None,
        metavar="PATH",
        help="instead of URLs, write a .bestpractices.json mapping to PATH; commit it "
        "to the target repo root and the OpenSSF BadgeApp seeds proposed answers from it "
        "(sidesteps URL length + multi-tab clobber entirely)",
    )
    parser.add_argument(
        "--section",
        default=None,
        help="badge level the URL targets (passing|silver|gold); "
        "default: inferred from the sheet filename. Fields not in this section are ignored.",
    )
    parser.add_argument(
        "--overrides",
        default=None,
        help="comma-separated globs of fields the proposals may overwrite (e.g. '*'); "
        "default: unforced (only fills blank fields)",
    )
    args = parser.parse_args(argv)

    sheet_path = Path(args.sheet)
    if not sheet_path.is_file():
        print(f"ERROR: sheet not found: {sheet_path}", file=sys.stderr)
        return 2

    rows = parse_sheet(sheet_path.read_text(encoding="utf-8"))
    # Expand the ``REPO`` shorthand to the real repo URL so proposals carry
    # clickable justifications, not the sheet's ``REPO/...`` abbreviation.
    rows = expand_rows(rows, repo_url_from_manifest(args))

    # JSON mode: no project id or section needed — the file lives in the target
    # repo and the BadgeApp links it to the registered project itself.
    if args.bestpractices_json:
        try:
            mapping = build_bestpractices_mapping(rows)
        except ProposalError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        out_path = Path(args.bestpractices_json)
        out_path.write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"# wrote {len(rows)} criteria to {out_path}")
        print(
            "# Commit this file as .bestpractices.json in the TARGET repo root; the OpenSSF "
            "BadgeApp reads it directly to seed proposed answers (no URL length or clobber "
            "limits). You remain the arbiter — the BadgeApp only proposes, you accept each."
        )
        return 0

    try:
        project_id = resolve_project_id(args)
    except ProposalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    section = args.section or infer_section(sheet_path)
    try:
        urls = build_urls(project_id, rows, args.max_url_len, args.overrides, section)
    except ProposalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    forced = f"overrides={args.overrides}" if args.overrides else "unforced (blank fields only)"
    if len(urls) == 1:
        print(f"# {len(rows)} criteria -> 1 proposal URL for project {project_id} ({forced}):")
        print(urls[0])
    else:
        per = _chunk_sizes(rows, urls, args)
        print(
            f"# {len(rows)} criteria -> {len(urls)} proposal URLs for project "
            f"{project_id} ({forced}); open EACH ({per}):"
        )
        print(
            "\n"
            "!!! ==================================================================== !!!\n"
            "!!! OPEN AND SAVE EACH URL ONE AT A TIME, SEQUENTIALLY.                   !!!\n"
            "!!! Do NOT open them all at once. Every URL edits the SAME section form,  !!!\n"
            "!!! so if several tabs are open together each loads a stale all-'?' form  !!!\n"
            "!!! and a later save CLOBBERS the answers you saved from an earlier tab.  !!!\n"
            "!!! Open URL 1, review + SAVE, close it, THEN open URL 2, and so on.      !!!\n"
            "!!! (Or use --bestpractices-json to avoid the split entirely.)            !!!\n"
            "!!! ==================================================================== !!!"
        )
        for n, url in enumerate(urls, 1):
            print(f"\n## URL {n} of {len(urls)} — save this one before opening the next")
            print(url)

    print(
        "\n# You are the arbiter: open each URL, review every HIGHLIGHTED proposal, "
        "and accept or ignore it. Nothing is written until you save in the UI; "
        "existing answers are left untouched unless --overrides was passed."
    )
    return 0


def _chunk_sizes(
    rows: list[tuple[str, str, str]],
    urls: list[str],
    args: argparse.Namespace,
) -> str:
    """Human-readable count of how many criteria each URL carries."""
    counts = [url.count("_status=") for url in urls]
    return ", ".join(f"URL {i}: {c}" for i, c in enumerate(counts, 1))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
