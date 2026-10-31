"""The rules must never see the answer key; only models/backtest/ may read it."""
import json

from scripts import check_answer_key_isolation as iso


def test_repo_is_clean():
    assert iso.MANIFEST.exists(), "run `make isolation` (dbt parse) first"
    assert iso.lineage_leaks(json.loads(iso.MANIFEST.read_text())) == []
    assert iso.text_leaks() == []


def _manifest(rule_depends_on: list[str]) -> dict:
    return {
        "sources": {"source.p.answer_key.fraud_cases": {"source_name": "answer_key"},
                    "source.p.raw.transactions": {"source_name": "raw"}},
        "nodes": {
            "model.p.bt_cases": {"original_file_path": "models/backtest/bt_cases.sql",
                                 "depends_on": {"nodes": ["source.p.answer_key.fraud_cases"]}},
            "model.p.rule_x": {"original_file_path": "models/rules/rule_x.sql",
                               "depends_on": {"nodes": rule_depends_on}},
        },
    }


def test_lineage_check_catches_a_rule_that_reads_the_backtest():
    leaks = iso.lineage_leaks(_manifest(["model.p.bt_cases"]))
    assert leaks == [("models/rules/rule_x.sql", "source.p.answer_key.fraud_cases")]


def test_lineage_check_allows_raw_only_rules():
    assert iso.lineage_leaks(_manifest(["source.p.raw.transactions"])) == []


def test_text_check_catches_a_mention(tmp_path):
    (tmp_path / "dbt" / "models" / "rules").mkdir(parents=True)
    (tmp_path / "dbt" / "macros").mkdir(parents=True)
    for d in ("generator", "loader", "scripts"):
        (tmp_path / d).mkdir()
    (tmp_path / "dbt" / "models" / "rules" / "sneaky.sql").write_text("select * from answer_key.fraud_cases")
    assert iso.text_leaks(tmp_path) == ["dbt/models/rules/sneaky.sql"]
