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
