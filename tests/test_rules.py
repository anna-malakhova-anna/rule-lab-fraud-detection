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
    macro = (ROOT / "dbt" / "macros" / "rule_ids.sql").read_text()
    assert set(re.findall(r"'(R\d+_[a-z0-9_]+)'", macro)) == set(RULES)


def test_rule_config_is_complete():
    for rid, r in RULES.items():
        assert r["rationale"].strip() and r["action"] in {"allow", "rfi", "hold", "block"}
        assert r["comparator"] in {">=", "<="}
        assert len(r["sweep"]) >= 5, f"{rid}: the sweep needs 5+ cutoffs"
        assert r["threshold"] in r["sweep"], f"{rid}: the configured cutoff must be a sweep point"
        assert r["status"] in {"champion", "challenger"}
        if r["status"] == "champion":
            assert not r.get("tune") and not r.get("effective_from_alarm"), f"{rid}: champion rules are fixed"


def test_gates_come_from_config():
    for rid, r in RULES.items():
        sql = (CAND / f"cand_{rid}.sql").read_text()
        for param in r["params"]:
            assert f"rule_param('{rid}', '{param}')" in sql, f"{rid}: gate {param} not read from config"
        where = sql.split("where", 1)[-1]
        # "> 0" is an existence check, not a threshold; any other number must come from config.
        literals = [x for x in re.findall(r"[<>=]=?\s*(\d+(?:\.\d+)?)\b", where) if float(x) != 0]
        assert not literals, f"{rid}: literal threshold(s) {literals} in the WHERE clause"


def test_rule_output_contract(con):
    cols = [r[0] for r in con.execute("describe rules.rule_hits").fetchall()]
    assert cols[:5] == ["rule_id", "entity_id", "event_time", "action", "reason"]
    for rid in RULES:
        rcols = [r[0] for r in con.execute(f"describe rules.rule_{rid}").fetchall()]
        assert rcols[:5] == cols[:5], rid
    actions = {r[0] for r in con.execute("select distinct action from rules.rule_hits").fetchall()}
    assert actions <= {"allow", "rfi", "hold", "block"}


def test_seeds_match_yaml(con):
    seeded = {r[0]: r[1] for r in con.execute("select rule_id, threshold from config.cfg_rules").fetchall()}
    assert seeded == {rid: float(r["threshold"]) for rid, r in RULES.items()}


def test_escalation_only_on_strong_hits(con):
    for rid, r in RULES.items():
        esc = r.get("escalate")
        if not esc:
            continue
        assert esc["action"] in {"hold", "block"} and esc["action"] != r["action"]
        op = r["comparator"]
        # Escalated exactly when the score passes `at` and the candidate is eligible.
        bad = con.execute(f"""
            select count(*) from rules.rule_hits
            where rule_id = ? and ((action = ?) <> (score {op} ? and escalation_eligible))""",
            [rid, esc["action"], esc["at"]]).fetchone()[0]
        assert bad == 0, rid


def test_reason_codes_are_unique_and_emitted(con):
    codes = [r["reason_code"] for r in RULES.values()]
    assert len(codes) == len(set(codes)) and all(re.fullmatch(r"[A-Z][A-Z0-9_]+", c) for c in codes)
    missing = con.execute("""
        select rule_id, count(*) from rules.rule_hits
        where reason_code is null or evidence is null or json_type(evidence) <> 'OBJECT' group by 1""").fetchall()
    assert missing == []
