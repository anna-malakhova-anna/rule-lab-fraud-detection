"""Reported numbers match the warehouse; the site carries nothing third-party."""
from scripts import render_results, site_check
from scripts.common import ROOT


def test_readme_and_memo_match_warehouse(con):
    rendered = render_results.render()
    for path, text in rendered.items():
        assert path.read_text() == text, f"{path.name} is stale: run `make results`"


def test_memos_are_marked_draft():
    for p in (ROOT / "docs" / "memo").glob("*.md"):
        assert "DRAFT" in p.read_text().splitlines()[0], p.name


def test_earlier_phase_docs_are_frozen_not_regenerated():
    for name in ("memo/rule-change-memo-phase1-DRAFT.md", "memo/rule-change-memo-phase2-DRAFT.md",
                 "investigations/INV-001-ach-debit-returns.md"):
        text = (ROOT / "docs" / name).read_text()
        assert ":start -->" not in text and "FROZEN" in text, name


def test_site_has_no_third_party_material():
    assert (ROOT / "site" / "index.html").exists(), "run `make site` first"
    assert site_check.problems() == []


def test_site_check_refuses_images_and_remote_assets(tmp_path):
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    (tmp_path / "index.html").write_text('<img src="x"><script src="https://cdn.example/x.js"></script>')
    found = site_check.problems(tmp_path)
    assert any("image file" in f for f in found)
    assert any("<img>" in f for f in found)
    assert any("external script" in f for f in found)


def test_no_real_company_or_personal_context_in_repo():
    banned = ["interview", "recruit", "hiring", "job application"]
    for p in list(ROOT.glob("*.md")) + list((ROOT / "docs").rglob("*.md")) + list((ROOT / "site").rglob("*.html")):
        text = p.read_text().lower()
        for word in banned:
            assert word not in text, f"{p.name} mentions '{word}'"


def test_site_has_every_page():
    for page in ("index", "tradeoffs", "types", "monitoring", "limitations", "glossary"):
        assert (ROOT / "site" / f"{page}.html").exists(), page
    assert len(list((ROOT / "site" / "types").glob("*.html"))) == 7


def test_duckdb_pinned_below_2():
    import duckdb
    assert int(duckdb.__version__.split(".")[0]) < 2, "see ADR-017"
