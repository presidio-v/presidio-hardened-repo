# SPDX-License-Identifier: MIT
# Copyright (c) 2026 PRESIDIO Group
"""Tests for answersheet_to_proposal — parsing, normalization, URL building."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import answersheet_to_proposal as a2p  # noqa: E402

SAMPLE = """\
# Header prose that is not a table.

## Basics

| Criterion | Status | Justification / URL |
|---|---|---|
| `description_good` | **Met** | See `REPO#readme` for the pitch. |
| `floss_license_osi` | **Met** | `MIT` is OSI-approved. |
| `release_notes_vulns` | **N/A** | No security release yet. |
| `crypto.random` | **Unmet (pending harness)** | Not implemented. |
| `bus_factor` (SHOULD) | **Met** | Backed by the steward org. |

Some closing prose, and a stray | pipe | that is not a real row header.
"""


def test_parse_sheet_basic_tuples() -> None:
    rows = a2p.parse_sheet(SAMPLE)
    assert rows == [
        ("description_good", "Met", "See `REPO#readme` for the pitch."),
        ("floss_license_osi", "Met", "`MIT` is OSI-approved."),
        ("release_notes_vulns", "N/A", "No security release yet."),
        ("crypto_random", "Unmet", "Not implemented."),
        ("bus_factor", "Met", "Backed by the steward org."),
    ]


def test_parse_skips_header_and_separator() -> None:
    rows = a2p.parse_sheet(SAMPLE)
    names = [r[0] for r in rows]
    assert "criterion" not in names
    assert len(rows) == 5


def test_parse_alternate_header_answer_column() -> None:
    sheet = (
        "| Criterion | Answer | Justification |\n"
        "|---|---|---|\n"
        "| `dco` | **Met** | Signed-off enforced. |\n"
    )
    assert a2p.parse_sheet(sheet) == [("dco", "Met", "Signed-off enforced.")]


def test_parse_unescapes_pipes_in_justification() -> None:
    sheet = (
        "| Criterion | Status | Justification |\n"
        "|---|---|---|\n"
        "| `test` | **Met** | run a \\| b then c. |\n"
    )
    assert a2p.parse_sheet(sheet)[0][2] == "run a | b then c."


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("**Met**", "Met"),
        ("Met", "Met"),
        ("**N/A**", "N/A"),
        ("N-A", "N/A"),
        ("**Unmet**", "Unmet"),
        ("**Unmet (pending KYB)**", "Unmet"),
        ("pending review", "Unmet"),
        ("?", "?"),
        ("unknown", "?"),
        ("", "?"),
        ("   ", "?"),
        ("garbage", "?"),
    ],
)
def test_normalize_status(cell: str, expected: str) -> None:
    assert a2p.normalize_status(cell) == expected


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ("`description_good`", "description_good"),
        ("`crypto.random`", "crypto_random"),
        ("`floss-license-osi`", "floss_license_osi"),
        ("`bus_factor` (SHOULD)", "bus_factor"),
        ("plain_name", "plain_name"),
        ("**Basics — documentation**", None),
        ("Criterion", "criterion"),
        ("", None),
        ("123bad", None),
    ],
)
def test_normalize_criterion(cell: str, expected: str | None) -> None:
    assert a2p.normalize_criterion(cell) == expected


def test_build_url_single_and_encoding() -> None:
    rows = [("crypto_random", "N/A", "See https://x.example/a b page")]
    urls = a2p.build_urls(99, rows)
    assert len(urls) == 1
    url = urls[0]
    assert url.startswith("https://www.bestpractices.dev/projects/99/choose/edit?")
    # Status is URL-encoded; N/A -> N%2FA.
    assert "crypto_random_status=N%2FA" in url
    # Justification is URL-encoded: spaces -> +, ':' and '/' escaped.
    assert "crypto_random_justification=" in url
    query = parse_qs(urlsplit(url).query)
    assert query["crypto_random_status"] == ["N/A"]
    assert query["crypto_random_justification"] == ["See https://x.example/a b page"]


def test_build_url_question_mark_encoded() -> None:
    urls = a2p.build_urls(7, [("maintained", "?", "")])
    assert "maintained_status=%3F" in urls[0]
    # No justification param when the text is empty.
    assert "maintained_justification=" not in urls[0]


def test_build_url_overrides_prefix_present_in_every_chunk() -> None:
    rows = [(f"crit_{i}", "Met", "x" * 50) for i in range(20)]
    urls = a2p.build_urls(3, rows, max_url_len=400, overrides="*")
    assert len(urls) > 1
    for url in urls:
        assert "overrides=%2A" in url  # '*' url-encoded


def test_build_url_empty_rows_errors() -> None:
    with pytest.raises(a2p.ProposalError):
        a2p.build_urls(1, [])


def test_chunking_covers_all_criteria_and_wellformed() -> None:
    rows = [(f"crit_{i:02d}", "Met", "just " * 20) for i in range(30)]
    urls = a2p.build_urls(500, rows, max_url_len=800)
    assert len(urls) > 1
    seen: list[str] = []
    for url in urls:
        split = urlsplit(url)
        assert split.scheme == "https"
        assert split.path == "/projects/500/choose/edit"
        query = parse_qs(split.query)
        seen.extend(k[: -len("_status")] for k in query if k.endswith("_status"))
    assert sorted(seen) == sorted(c for c, _, _ in rows)


def test_chunking_single_oversized_criterion_gets_its_own_url() -> None:
    rows = [("big_one", "Met", "z" * 5000), ("small", "Met", "ok")]
    urls = a2p.build_urls(1, rows, max_url_len=200)
    assert len(urls) == 2
    joined = " ".join(urls)
    assert "big_one_status=" in joined
    assert "small_status=" in joined


def _ns(**kw: object) -> argparse.Namespace:
    base = {"id": None, "manifest": "hardening.toml", "repo_path": "."}
    base.update(kw)
    return argparse.Namespace(**base)


def test_resolve_id_override() -> None:
    assert a2p.resolve_project_id(_ns(id=13746)) == 13746


def test_resolve_id_from_manifest(tmp_path: Path) -> None:
    (tmp_path / "hardening.toml").write_text("[badge]\nbestpractices_id = 4242\n", encoding="utf-8")
    assert a2p.resolve_project_id(_ns(repo_path=str(tmp_path))) == 4242


def test_resolve_id_zero_errors(tmp_path: Path) -> None:
    (tmp_path / "hardening.toml").write_text("[badge]\nbestpractices_id = 0\n", encoding="utf-8")
    with pytest.raises(a2p.ProposalError, match="register the project"):
        a2p.resolve_project_id(_ns(repo_path=str(tmp_path)))


def test_resolve_id_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(a2p.ProposalError, match="manifest not found"):
        a2p.resolve_project_id(_ns(repo_path=str(tmp_path)))


def test_resolve_id_absolute_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "custom.toml"
    manifest.write_text("[badge]\nbestpractices_id = 11\n", encoding="utf-8")
    assert a2p.resolve_project_id(_ns(manifest=str(manifest))) == 11


def test_main_single_url(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n"
        "|---|---|---|\n"
        "| `description_good` | **Met** | Good desc. |\n",
        encoding="utf-8",
    )
    rc = a2p.main(["--sheet", str(sheet), "--id", "13746"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 proposal URL" in out
    assert "projects/13746/choose/edit" in out
    assert "arbiter" in out


def test_main_multi_url_reports_chunks(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lines = ["| Criterion | Status | Justification |", "|---|---|---|"]
    lines += [f"| `crit_{i:02d}` | **Met** | {'x' * 80} |" for i in range(20)]
    sheet = tmp_path / "sheet.md"
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rc = a2p.main(["--sheet", str(sheet), "--id", "9", "--max-url-len", "500"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "proposal URLs" in out
    assert "URL 1 of" in out


def test_main_overrides_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n|---|---|---|\n| `dco` | **Met** | x |\n",
        encoding="utf-8",
    )
    rc = a2p.main(["--sheet", str(sheet), "--id", "5", "--overrides", "*"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "overrides=*" in out
    assert "overrides=%2A" in out


def test_main_sheet_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    rc = a2p.main(["--sheet", "/no/such/sheet.md", "--id", "1"])
    assert rc == 2
    assert "sheet not found" in capsys.readouterr().err


def test_main_id_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n|---|---|---|\n| `dco` | **Met** | x |\n",
        encoding="utf-8",
    )
    (tmp_path / "hardening.toml").write_text("[badge]\nbestpractices_id = 0\n", encoding="utf-8")
    rc = a2p.main(["--sheet", str(sheet), "--repo-path", str(tmp_path)])
    assert rc == 2
    assert "register the project" in capsys.readouterr().err


def test_main_empty_sheet_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sheet = tmp_path / "empty.md"
    sheet.write_text("# no tables here\n", encoding="utf-8")
    rc = a2p.main(["--sheet", str(sheet), "--id", "1"])
    assert rc == 2
    assert "no criteria parsed" in capsys.readouterr().err


def test_resolve_id_non_integer_manifest(tmp_path: Path) -> None:
    (tmp_path / "hardening.toml").write_text(
        '[badge]\nbestpractices_id = "abc"\n', encoding="utf-8"
    )
    with pytest.raises(a2p.ProposalError, match="not an integer"):
        a2p.resolve_project_id(_ns(repo_path=str(tmp_path)))


# --- max-url-len default (Fix 1a: 6000 -> 7000) -----------------------------


def test_build_urls_default_max_len_is_7000() -> None:
    assert inspect.signature(a2p.build_urls).parameters["max_url_len"].default == 7000


def test_default_max_len_keeps_one_url_where_6000_would_split() -> None:
    # Two ~3.3 KB criteria total ~6.7 KB: fits in one URL at the 7000 default,
    # but the old 6000 cap would have split them into two.
    rows = [("crit_0", "Met", "z" * 3300), ("crit_1", "Met", "z" * 3300)]
    assert len(a2p.build_urls(1, rows)) == 1
    assert len(a2p.build_urls(1, rows, max_url_len=6000)) == 2


def test_cli_default_max_len_single_url(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    lines = ["| Criterion | Status | Justification |", "|---|---|---|"]
    lines += [f"| `crit_{i}` | **Met** | {'z' * 3300} |" for i in range(2)]
    sheet = tmp_path / "sheet.md"
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rc = a2p.main(["--sheet", str(sheet), "--id", "9"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "1 proposal URL" in out  # not split at the 7000 default


# --- multi-URL clobber warning (Fix 1b) -------------------------------------


def test_multi_url_prints_one_at_a_time_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lines = ["| Criterion | Status | Justification |", "|---|---|---|"]
    lines += [f"| `crit_{i:02d}` | **Met** | {'x' * 80} |" for i in range(20)]
    sheet = tmp_path / "sheet.md"
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rc = a2p.main(["--sheet", str(sheet), "--id", "9", "--max-url-len", "500"])
    out = capsys.readouterr().out
    assert rc == 0
    # Loud, explicit sequential-save warning.
    assert "ONE AT A TIME" in out
    assert "CLOBBER" in out
    assert "SAME section form" in out
    # Existing per-URL numbering is kept.
    assert "URL 1 of" in out


def test_single_url_has_no_clobber_warning(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n|---|---|---|\n| `dco` | **Met** | x |\n",
        encoding="utf-8",
    )
    rc = a2p.main(["--sheet", str(sheet), "--id", "9"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ONE AT A TIME" not in out


# --- .bestpractices.json output mode (Fix 1c) -------------------------------


def test_build_bestpractices_mapping_values() -> None:
    rows = [
        ("description_good", "Met", "See https://x.example/a b for the pitch."),
        ("release_notes_vulns", "N/A", "none yet"),
        ("crypto_random", "Unmet", "not done"),
        ("maintained", "?", ""),
    ]
    mapping = a2p.build_bestpractices_mapping(rows)
    assert mapping["description_good_status"] == "Met"
    # Justification is a PLAIN string — not url-encoded (spaces/slashes intact).
    assert mapping["description_good_justification"] == "See https://x.example/a b for the pitch."
    assert mapping["release_notes_vulns_status"] == "N/A"  # literal, not N%2FA
    assert mapping["crypto_random_status"] == "Unmet"
    assert mapping["maintained_status"] == "?"  # literal, not %3F
    # No justification key when the cell is empty.
    assert "maintained_justification" not in mapping


def test_build_bestpractices_mapping_empty_errors() -> None:
    with pytest.raises(a2p.ProposalError):
        a2p.build_bestpractices_mapping([])


def test_main_bestpractices_json_writes_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n"
        "|---|---|---|\n"
        "| `description_good` | **Met** | See https://x.example/a b page. |\n"
        "| `release_notes_vulns` | **N/A** | none yet |\n"
        "| `maintained` | **?** |  |\n",
        encoding="utf-8",
    )
    out_file = tmp_path / ".bestpractices.json"
    rc = a2p.main(["--sheet", str(sheet), "--id", "9", "--bestpractices-json", str(out_file)])
    out = capsys.readouterr().out
    assert rc == 0
    assert str(out_file) in out
    assert ".bestpractices.json" in out
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data["description_good_status"] == "Met"
    assert data["description_good_justification"] == "See https://x.example/a b page."
    assert data["release_notes_vulns_status"] == "N/A"
    assert data["maintained_status"] == "?"
    assert "maintained_justification" not in data
    # No URL params leaked in — this is not the URL mode.
    assert "%2F" not in out_file.read_text(encoding="utf-8")


def test_main_bestpractices_json_needs_no_project_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # JSON mode must not require a resolvable project id (id 0 in the manifest).
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "| Criterion | Status | Justification |\n|---|---|---|\n| `dco` | **Met** | x |\n",
        encoding="utf-8",
    )
    (tmp_path / "hardening.toml").write_text("[badge]\nbestpractices_id = 0\n", encoding="utf-8")
    out_file = tmp_path / ".bestpractices.json"
    rc = a2p.main(
        ["--sheet", str(sheet), "--repo-path", str(tmp_path), "--bestpractices-json", str(out_file)]
    )
    assert rc == 0
    assert json.loads(out_file.read_text(encoding="utf-8"))["dco_status"] == "Met"


def test_main_bestpractices_json_empty_sheet_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sheet = tmp_path / "empty.md"
    sheet.write_text("# no tables here\n", encoding="utf-8")
    out_file = tmp_path / ".bestpractices.json"
    rc = a2p.main(["--sheet", str(sheet), "--id", "1", "--bestpractices-json", str(out_file)])
    assert rc == 2
    assert "no criteria parsed" in capsys.readouterr().err
    assert not out_file.exists()
