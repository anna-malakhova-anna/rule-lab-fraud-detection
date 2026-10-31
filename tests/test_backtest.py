"""The backtest keeps tuning and grading apart and its numbers add up."""
from scripts.common import ROOT


def test_challenger_is_tuned_on_training_months_with_known_labels_only():
    sql = (ROOT / "dbt" / "models" / "backtest" / "bt_challenger_thresholds.sql").read_text()
    assert "m.period = 'train'" in sql and "'test'" not in sql
    assert "bt_sweep_metrics_known" in sql and "ref('bt_sweep_metrics')" not in sql


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


def test_known_labels_never_exceed_all_labels(con):
    rows = con.execute("""
        select k.strategy_id, k.period, k.cases, f.cases, k.loss_prevented, f.loss_prevented
        from backtest.bt_sweep_metrics_known k join backtest.bt_sweep_metrics f using (strategy_id, period)""").fetchall()
    for s, p, kc, fc, kp, fp in rows:
        assert kc <= fc and kp <= fp + 0.01, (s, p)


def test_challenger_keeps_every_champion_hit(con):
    missing = con.execute("""
        select count(*) from backtest.bt_strategy_hits c
        where c.strategy_id = 'champion' and not exists (
            select 1 from backtest.bt_strategy_hits x
            where x.strategy_id = 'challenger' and x.txn_id = c.txn_id and x.rule_id = c.rule_id)""").fetchone()[0]
    assert missing == 0


def test_alarm_driven_rule_starts_at_its_live_date(con):
    early = con.execute("""
        select count(*) from backtest.bt_strategy_hits h
        join monitoring.mon_rule_effective_from e using (rule_id)
        where h.strategy_id = 'challenger' and h.event_time < e.effective_from""").fetchone()[0]
    assert early == 0
    start = con.execute("select window_start from config.cfg_window").fetchone()[0]
    for detected, live in con.execute("select detected_at, effective_from from monitoring.mon_rule_effective_from").fetchall():
        assert detected is not None and live > detected and detected.date() >= start


def test_alarm_is_found_without_labels():
    sql = "".join(p.read_text() for p in (ROOT / "dbt" / "models" / "monitoring").glob("*.sql"))
    assert "answer_key" not in sql and "bt_" not in sql


def test_month_12_pattern_still_raises_an_alarm(con):
    first = con.execute("""
        select min(week) from monitoring.mon_weekly_alarms
        where is_alarm and series = 'ach_debit_in:unauthorized'
          and week >= (select window_start from config.cfg_window)""").fetchone()[0]
    assert first is not None


def test_honest_defaults_are_never_fraud_cases(con):
    overlap = con.execute("""
        select count(*) from answer_key.business_profile p
        join answer_key.fraud_cases c using (business_id) where p.archetype = 'failing_business'""").fetchone()[0]
    assert overlap == 0
    sql = (ROOT / "dbt" / "models" / "backtest" / "bt_credit_losses.sql").read_text()
    assert "loss_prevented" not in sql, "credit losses must not feed fraud prevented"
