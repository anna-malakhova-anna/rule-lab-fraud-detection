"""The inventory, change log and quarterly review stay true to config and to what the bank knew (module F)."""
from scripts.common import ROOT, load_yaml

RULES = load_yaml("rules.yaml")["rules"]
CHANGES = load_yaml("rule_changes.yaml")["changes"]
GOV = load_yaml("governance.yaml")


def test_every_rule_has_an_owner_and_a_change_log():
    logged = {c["rule_id"] for c in CHANGES}
    assert logged == set(RULES)
    for rid, r in RULES.items():
        assert r["owner"].strip(), rid


def test_change_log_matches_the_running_config():
    """A cutoff or action change that skips the change log fails here."""
    for rid, r in RULES.items():
        entries = [c for c in CHANGES if c["rule_id"] == rid]
        last_threshold = [c["threshold"] for c in entries if "threshold" in c][-1]
        last_action = [c["action"] for c in entries if "action" in c][-1]
        assert float(last_threshold) == float(r["threshold"]), f"{rid}: cutoff {r['threshold']} has no change-log entry"
        assert last_action == r["action"], f"{rid}: action {r['action']} has no change-log entry"
        assert entries[0]["change"] == "added", rid


def test_change_log_cites_decisions_that_exist():
    adrs = {p.name.split("-")[0] + "-" + p.name.split("-")[1] for p in (ROOT / "docs" / "decisions").glob("ADR-*.md")}
    for c in CHANGES:
        assert c["decision"] in adrs, c
        assert c["change"] in {"added", "threshold", "action", "scope", "status", "retired"}, c
        assert c["backtest"].strip(), c


def test_review_lags_name_running_rules():
    for rid in GOV["lag_quarters"]:
        assert RULES[rid]["status"] in ("champion", "challenger"), rid


def test_leave_one_out_drops_exactly_one_rule(con):
    rows = con.execute("""
        select s.rule_id,
               (select count(*) from backtest.bt_strategy_hits h where h.strategy_id = s.strategy_id and h.rule_id = s.rule_id),
               (select count(*) from backtest.bt_strategy_hits h where h.strategy_id = s.strategy_id),
               (select count(*) from backtest.bt_strategy_hits h where h.strategy_id = 'challenger' and h.rule_id <> s.rule_id)
        from backtest.bt_strategies s where s.strategy_kind = 'leave_one_out'""").fetchall()
    assert rows
    for rule, own, total, expected in rows:
        assert own == 0 and total == expected, rule


def test_quarterly_review_covers_every_running_rule_every_quarter(con):
    rows = con.execute("select rule_id, quarter, lag_quarters, recommendation from backtest.gov_rule_quarterly").fetchall()
    running = {r[0] for r in con.execute(
        "select distinct rule_id from backtest.bt_strategy_hits where strategy_id = 'challenger'").fetchall()}
    quarters = {r[1] for r in rows}
    assert {r[0] for r in rows} == running and len(rows) == len(running) * len(quarters) == len(quarters) * len(running)
    assert {r[3] for r in rows} <= {"keep", "retune", "retire candidate", "investigate drift", "too early"}
    # A rule judged on older alerts has nothing to judge until enough quarters have passed.
    first = sorted(quarters)
    for rid, q, lag, rec in rows:
        assert (rec == "too early") == (first.index(q) < lag), (rid, q)


def test_review_counts_only_labels_known_by_the_review_day(con):
    over = con.execute("""
        select count(*) from backtest.gov_rule_quarterly q
        where q.alerts_on_known_fraud > (
            select count(distinct g.txn_id)
            from backtest.bt_strategy_graded g join backtest.bt_cases c using (case_id)
            where g.strategy_id = 'challenger' and list_contains(string_split(g.rules, ','), q.rule_id)
              and c.label_known_at <= q.reviewed_on)""").fetchone()[0]
    assert over == 0


def test_inventory_lists_every_rule(con):
    inv = {r[0] for r in con.execute("select rule_id from backtest.gov_rule_inventory").fetchall()}
    assert inv == set(RULES)
