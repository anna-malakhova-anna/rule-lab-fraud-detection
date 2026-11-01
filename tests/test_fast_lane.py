"""The fast lane only ever softens the configured rules, for eligible businesses, below its cap (module E)."""
from scripts.common import load_yaml

FL = load_yaml("rules.yaml")["fast_lane"]


def test_fast_lane_only_softens_configured_rules_below_the_cap(con):
    bad = con.execute("""
        select count(*)
        from backtest.bt_strategy_hits f
        join backtest.bt_strategies s using (strategy_id)
        join backtest.bt_strategy_hits c on c.strategy_id = 'challenger' and c.txn_id = f.txn_id and c.rule_id = f.rule_id
        where s.strategy_kind = 'fast_lane' and f.action <> c.action
          and (f.action <> ? or f.rule_id not in (select rule_id from config.cfg_fast_lane_rules)
               or (s.cutoff is not null and f.amount >= s.cutoff))""", [FL["soften_to"]]).fetchone()[0]
    assert bad == 0
    # Same alerts as the challenger: the fast lane changes actions, it never drops an alert.
    counts = con.execute("""
        select strategy_id, count(*) from backtest.bt_strategy_hits
        where strategy_id = 'challenger' or strategy_id like 'fast_lane:%' group by 1""").fetchall()
    assert len({n for _, n in counts}) == 1


def test_softened_alerts_land_only_on_eligible_businesses(con):
    young = con.execute("""
        select count(*)
        from backtest.bt_strategy_hits f
        join backtest.bt_strategy_hits c on c.strategy_id = 'challenger' and c.txn_id = f.txn_id and c.rule_id = f.rule_id
        join staging.stg_businesses b on b.business_id = f.business_id
        where f.strategy_id = 'fast_lane:none' and f.action <> c.action
          and f.event_time < b.open_date + to_days(?)""", [FL["min_tenure_days"]]).fetchone()[0]
    assert young == 0


def test_a_higher_cap_softens_more(con):
    rows = con.execute("""
        select max_amount, good_holds_avoided from backtest.bt_fast_lane_tradeoff
        where strategy_kind = 'fast_lane' and period = 'test' order by max_amount nulls last""").fetchall()
    avoided = [r[1] for r in rows]
    assert avoided == sorted(avoided) and avoided[0] > 0


def test_todays_decline_bar_is_the_challenger(con):
    cols = "loss_prevented, alerts, good_businesses_flagged, good_applicants_declined, reviews, net_value"
    today = con.execute(f"select period, {cols} from backtest.bt_strategy_metrics where strategy_id = 'decline_at:3' order by 1").fetchall()
    challenger = con.execute(f"select period, {cols} from backtest.bt_strategy_metrics where strategy_id = 'challenger' order by 1").fetchall()
    assert len(today) == len(challenger)
    for a, b in zip(today, challenger):
        assert a[0] == b[0] and all(abs(x - y) < 1e-6 for x, y in zip(a[1:], b[1:]))


def test_never_declining_declines_nobody(con):
    declined = con.execute("""
        select count(*) from backtest.bt_strategy_hits
        where strategy_id = 'decline_at:never' and txn_type = 'application' and action = 'block'""").fetchone()[0]
    assert declined == 0
