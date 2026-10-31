"""Rules follow one contract and take their thresholds from config, never from literals."""
import re

from scripts.common import ROOT, load_yaml

RULES = load_yaml("rules.yaml")["rules"]
CAND = ROOT / "dbt" / "models" / "rules" / "candidates"


def test_every_configured_rule_has_models_and_vice_versa():
    models = {p.stem.removeprefix("cand_") for p in CAND.glob("cand_*.sql")}
    assert models == set(RULES)
    for rid in RULES:
        assert (ROOT / "dbt" / "models" / "rules" / f"rule_{rid}.sql").exists()


def test_rule_config_is_complete():
    for rid, r in RULES.items():
        assert r["rationale"].strip() and r["action"] in {"allow", "rfi", "hold", "block"}
        assert r["comparator"] in {">=", "<="}
        assert len(r["sweep"]) >= 5, f"{rid}: the sweep needs 5+ cutoffs"
        assert r["threshold"] in r["sweep"], f"{rid}: the champion cutoff must be a sweep point"


def test_gates_come_from_config():
    for rid, r in RULES.items():
        sql = (CAND / f"cand_{rid}.sql").read_text()
        for param in r["params"]:
            assert f"rule_param('{rid}', '{param}')" in sql, f"{rid}: gate {param} not read from config"
        where = sql.split("where", 1)[-1]
        literals = re.findall(r"[<>=]=?\s*(\d+(?:\.\d+)?)\b", where)
        assert not literals, f"{rid}: literal threshold(s) {literals} in the WHERE clause"


def test_rule_output_contract(con):
    cols = [r[0] for r in con.execute("describe rules.rule_hits").fetchall()]
    assert cols[:5] == ["rule_id", "entity_id", "event_time", "action", "reason"]
    actions = {r[0] for r in con.execute("select distinct action from rules.rule_hits").fetchall()}
    assert actions <= {"allow", "rfi", "hold", "block"}


def test_seeds_match_yaml(con):
    seeded = {r[0]: r[1] for r in con.execute("select rule_id, threshold from config.cfg_rules").fetchall()}
    assert seeded == {rid: float(r["threshold"]) for rid, r in RULES.items()}
