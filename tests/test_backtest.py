"""The backtest keeps tuning and grading apart and its numbers add up."""
from scripts.common import ROOT


def test_challenger_is_tuned_on_training_months_only():
    sql = (ROOT / "dbt" / "models" / "backtest" / "bt_challenger_thresholds.sql").read_text()
    assert "m.period = 'train'" in sql and "'test'" not in sql


def test_periods_split_at_month_12(con):
    start, train_end, end = con.execute("select window_start, train_end, window_end from config.cfg_window").fetchone()
    months = lambda a, b: (b.year - a.year) * 12 + b.month - a.month
    assert months(start, train_end) == 12 and months(start, end) == 18


def test_dollars_reconcile(con):
    rows = con.execute("""
        select strategy_id, period, loss_if_uncaught, loss_prevented + loss_missed
        from backtest.bt_strategy_metrics""").fetchall()
    for s, p, total, parts in rows:
        assert abs(total - parts) < 0.01, (s, p)


def test_loss_at_stake_matches_answer_key(con):
    key = con.execute("select sum(loss_if_uncaught) from backtest.bt_cases").fetchone()[0]
    graded = con.execute("select sum(loss_if_uncaught) from backtest.bt_strategy_metrics where strategy_id = 'champion'").fetchone()[0]
    assert abs(key - graded) < 0.01


def test_every_sweep_point_has_both_periods(con):
    n = con.execute("select count(*) from backtest.bt_sweep_strategies").fetchone()[0]
    m = con.execute("select count(*) from backtest.bt_sweep_metrics").fetchone()[0]
    assert m == 2 * n


def test_bootstrap_ranges_bracket_the_estimate(con):
    for s, metric, est, lo, hi in con.execute("select * from analysis.bootstrap_ci where strategy_id <> 'challenger_minus_champion'").fetchall():
        assert lo - 1e-9 <= est <= hi + 1e-9 or est == 0, (s, metric)


def test_challenger_never_holds_excluded_types(con):
    leaked = con.execute("""
        select count(*) from backtest.bt_strategy_hits h
        join config.cfg_challenger_scope x on x.rule_id = h.rule_id and x.excluded_txn_type = h.txn_type
        where h.strategy_id = 'challenger'""").fetchone()[0]
    assert leaked == 0


def test_challenger_scope_is_tuned_in_its_own_scope(con):
    rows = con.execute("""
        select t.rule_id, t.scope, x.rule_id is not null as has_scope
        from backtest.bt_challenger_thresholds t
        left join (select distinct rule_id from config.cfg_challenger_scope) x using (rule_id)""").fetchall()
    for rule_id, scope, has_scope in rows:
        assert scope == ("challenger" if has_scope else "as_written"), rule_id
