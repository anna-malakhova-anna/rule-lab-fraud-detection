"""Module C (instant payouts) and module D (vendor bake-off)."""
from scripts.common import ROOT, load_yaml


def test_instant_payouts_exist_only_after_launch(con):
    first, launch = con.execute("""
        select min(txn_time), (select instant_launch_date from config.cfg_window)
        from raw.transactions where txn_type = 'instant_payout'""").fetchone()
    assert first.date() >= launch


def test_instant_payouts_respect_the_cap(con):
    cap = load_yaml("generation.yaml")["instant_payouts"]["per_payout_cap"]
    assert con.execute("select max(amount) from raw.transactions where txn_type = 'instant_payout'").fetchone()[0] <= cap


def test_an_alert_on_an_instant_payout_itself_cannot_stop_it(con):
    """Champion credit on a still-instant loss only ever comes from an alert strictly before it."""
    bad = con.execute("""
        select count(*) from backtest.bt_loss_credit l
        where l.strategy_id = 'champion' and l.still_instant and l.prevents > 0
          and not exists (select 1 from backtest.bt_strategy_graded g
                          where g.strategy_id = 'champion' and g.case_id = l.case_id and g.event_time < l.txn_time)""").fetchone()[0]
    assert bad == 0


def test_controls_never_lose_fraud_dollars(con):
    rows = con.execute("select strategy_id, added_vs_today from backtest.bt_launch_controls").fetchall()
    assert all(added >= -0.01 for _, added in rows), rows


def test_launch_controls_stay_out_of_champion_and_challenger(con):
    leaked = con.execute("""
        select count(*) from backtest.bt_strategy_hits h join config.cfg_rules r using (rule_id)
        where h.strategy_id in ('champion', 'challenger') and r.status in ('launch_control', 'vendor')""").fetchone()[0]
    assert leaked == 0


def test_vendor_call_counts_follow_the_strategy(con):
    calls = {(v, s): n for v, s, n in con.execute("""
        select vendor, call_strategy, sum(calls) from backtest.bt_vendor_calls group by all""").fetchall()}
    for vendor in ("tallowmere", "quenchwire"):
        assert calls[(vendor, "risk_gated")] < calls[(vendor, "onboarding_only")] < calls[(vendor, "always")]


def test_vendor_cost_is_calls_times_price(con):
    prices = {k: v["cost_per_call"] for k, v in load_yaml("vendors.yaml")["vendors"].items()}
    for vendor, calls, cost in con.execute("select vendor, calls, vendor_cost from backtest.bt_vendor_bakeoff").fetchall():
        assert abs(cost - calls * prices[vendor]) < 0.01


def test_vendor_names_are_invented_and_flagged_as_such():
    text = (ROOT / "docs" / "vendors" / "vendor-bakeoff-DRAFT.md").read_text()
    assert "invented" in text and "DRAFT" in text.splitlines()[0]
