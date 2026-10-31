"""Every reported number, read from the warehouse in one place. The README, the memo and the site all use these
functions, so a number cannot drift between them.
"""
from __future__ import annotations

from scripts.common import connect

RULE_LABELS = {
    "R1_check_then_fast_out": "R1 Check money out fast",
    "R2_check_vs_own_baseline": "R2 Check far above own baseline",
    "R3_many_new_check_payers": "R3 Many new check payers",
    "R4_new_bank_details_first_payment": "R4 First payment to changed bank details",
    "R5_payee_amount_out_of_pattern": "R5 Payment far above usual for payee",
}


def _rows(sql: str, params: list | None = None) -> list[dict]:
    con = connect()
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    out = [dict(zip(cols, r)) for r in cur.fetchall()]
    con.close()
    return out


def challenger_cell(r: dict) -> str:
    """How the challenger runs a rule: its cutoff, plus any scope change."""
    if not r["is_kept"]:
        return "retired"
    cell = f"{r['comparator']} {r['challenger_cutoff']:g}"
    return cell + (f", excluding {r['excluded']}" if r["excluded"] else "")


def window() -> dict:
    return _rows("select * from config.cfg_window")[0]


def strategy_metrics(period: str = "test") -> dict[str, dict]:
    rows = _rows("select * from backtest.bt_strategy_metrics where period = ?", [period])
    return {r["strategy_id"]: r for r in rows}


def bootstrap() -> dict[tuple[str, str], dict]:
    return {(r["strategy_id"], r["metric"]): r for r in _rows("select * from analysis.bootstrap_ci")}


def challenger_thresholds() -> list[dict]:
    return _rows("""
        select r.rule_id, r.threshold as champion_cutoff, t.challenger_cutoff, t.is_kept, t.scope, r.comparator, r.action,
               (select string_agg(excluded_txn_type, ', ') from config.cfg_challenger_scope x where x.rule_id = r.rule_id) as excluded
        from config.cfg_rules r left join backtest.bt_challenger_thresholds t using (rule_id)
        order by r.rule_id""")


def sweep(period: str = "train") -> list[dict]:
    return _rows("""
        select m.*, s.scope, s.is_champion_cutoff,
               coalesce(t.challenger_cutoff = m.cutoff and t.scope = s.scope, false) as is_challenger_cutoff, r.comparator
        from backtest.bt_sweep_metrics m
        join backtest.bt_sweep_strategies s using (strategy_id)
        join config.cfg_rules r on r.rule_id = m.rule_id
        left join backtest.bt_challenger_thresholds t on t.rule_id = m.rule_id
        where m.period = ?
        order by m.rule_id, s.scope, m.cutoff""", [period])


def overlap(strategy: str = "champion") -> list[dict]:
    return _rows("""
        select rule_id, period, cases_detected, cases_only_this_rule, loss_in_cases_only_this_rule
        from backtest.bt_rule_overlap where strategy_id = ? and period is not null
        order by rule_id, period""", [strategy])


def harm_by_archetype(strategy: str = "champion") -> list[dict]:
    return _rows("""
        select archetype, sum(good_alerts) as good_alerts, sum(good_businesses) as good_business_rule_pairs,
               sum(good_dollar_days_held) as dollar_days
        from backtest.bt_good_customer_harm where strategy_id = ? and period = 'test'
        group by archetype order by good_alerts desc""", [strategy])


def harm_by_rule(strategy: str = "champion", period: str = "test") -> list[dict]:
    return _rows("""
        select rule_id, sum(good_alerts) as good_alerts from backtest.bt_good_customer_harm
        where strategy_id = ? and period = ? group by rule_id order by rule_id""", [strategy, period])


def payroll_by_rule(strategy: str = "champion") -> list[dict]:
    return _rows("""
        with per_rule as (
            select g.period, unnest(string_split(g.rules, ',')) as rule_id
            from backtest.bt_strategy_graded g
            where g.strategy_id = ? and g.label = 'good' and g.hold_days > 0 and g.txn_type = 'payroll'
              and g.period in ('train', 'test'))
        select rule_id, period, count(*) as payrolls_delayed from per_rule group by all order by 1, 2""", [strategy])


def typology_outcomes(strategy: str = "champion", period: str = "test") -> list[dict]:
    return _rows("""
        select typology, variant, count(*) as cases, count(*) filter (where detected) as detected,
               sum(loss_if_uncaught) as loss, sum(loss_prevented) as prevented,
               median(hours_to_first_hit) as median_hours_to_first_hit
        from backtest.bt_strategy_cases where strategy_id = ? and period = ?
        group by all order by 1, 2""", [strategy, period])


def weekly_reviews() -> list[dict]:
    return _rows("""
        select strategy_id, cast(date_trunc('week', business_date) as date) as week, avg(reviews) as avg_reviews,
               max(reviews) as max_reviews, any_value(capacity) as capacity,
               count(*) filter (where over_capacity) as days_over
        from backtest.bt_daily_reviews group by all order by strategy_id, week""")


def totals() -> dict:
    return _rows("""
        select (select count(*) from staging.stg_businesses) as businesses,
               (select count(*) from staging.stg_transactions) as transactions,
               (select count(*) from backtest.bt_cases) as cases,
               (select count(*) from backtest.bt_cases where period = 'test') as test_cases""")[0]


# ---------- formatting ----------

def usd(x: float) -> str:
    x = float(x or 0)
    if abs(x) >= 1e6:
        return f"${x / 1e6:,.2f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:,.0f}K"
    return f"${x:,.0f}"


def pct(x: float | None, digits: int = 0) -> str:
    return "n/a" if x is None else f"{100 * x:.{digits}f}%"


def num(x: float, digits: int = 0) -> str:
    return f"{float(x or 0):,.{digits}f}"


def ci(boot: dict, strategy: str, metric: str, fmt) -> str:
    b = boot[(strategy, metric)]
    return f"{fmt(b['estimate'])} ({fmt(b['p05'])} to {fmt(b['p95'])})"


def headline_rows() -> list[tuple[str, str, str]]:
    """(measure, champion, challenger) for the test months: the README table and the memo's numbers."""
    m, b = strategy_metrics("test"), bootstrap()
    ch, cl = m["champion"], m["challenger"]
    return [
        ("Fraud $ prevented (90% range)", ci(b, "champion", "loss_prevented", usd), ci(b, "challenger", "loss_prevented", usd)),
        ("Share of fraud $ prevented", ci(b, "champion", "dollar_recall", pct), ci(b, "challenger", "dollar_recall", pct)),
        ("Fraud cases detected", f"{ch['cases_detected']} of {ch['cases']}", f"{cl['cases_detected']} of {cl['cases']}"),
        ("Alerts that were fraud (precision)", pct(ch["precision"], 1), pct(cl["precision"], 1)),
        ("Good businesses flagged", num(ch["good_businesses_flagged"]), num(cl["good_businesses_flagged"])),
        ("Good businesses with money held", num(ch["good_businesses_held"]), num(cl["good_businesses_held"])),
        ("Payrolls delayed", num(ch["payrolls_delayed"]), num(cl["payrolls_delayed"])),
        ("Good-customer dollar-days held", usd(ch["good_dollar_days_held"]), usd(cl["good_dollar_days_held"])),
        ("Reviews per business day (avg / max)", f"{num(ch['reviews_per_day'], 1)} / {ch['reviews_max_day']}",
         f"{num(cl['reviews_per_day'], 1)} / {cl['reviews_max_day']}"),
        ("Days over review capacity", f"{ch['days_over_capacity']} of {ch['business_days']}",
         f"{cl['days_over_capacity']} of {cl['business_days']}"),
    ]


def markdown_table(header: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)
