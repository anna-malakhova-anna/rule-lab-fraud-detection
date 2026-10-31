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
    "R6_onboarding_shared_identity": "R6 Applicant shares identity with others",
    "R7_mule_fan_in_sweep": "R7 Many new senders, swept out",
    "R8_ato_new_device_sequence": "R8 New device, contact change, new payee",
    "R9_ach_pull_then_fast_out": "R9 ACH debit money out fast",
    "R10_credit_inflow_ramp": "R10 Inflows ramped before a credit decision",
    "R11_draw_then_fast_out": "R11 Credit draw money out fast",
    "R12_full_draw_after_increase": "R12 Line drawn to limit soon after increase",
}
TYPOLOGY_LABELS = {
    "check_deposit_fraud": "Check deposit fraud",
    "bec_vendor_change": "Vendor bank-detail change (BEC)",
    "synthetic_shell": "Synthetic / shell businesses",
    "money_mule": "Money mules",
    "account_takeover": "Account takeover",
    "ach_return_fraud": "ACH return fraud (emerging, month 12)",
    "credit_bust_out": "Credit bust-out",
}


def _rows(sql: str, params: list | None = None) -> list[dict]:
    con = connect()
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    out = [dict(zip(cols, r)) for r in cur.fetchall()]
    con.close()
    return out


def challenger_cell(r: dict) -> str:
    """How the challenger runs a rule: its cutoff, and when it starts if it answers an alarm."""
    if r["status"] == "challenger" and r["tune"] and not r["is_kept"]:
        return "not adopted"
    cell = f"{r['comparator']} {r['challenger_cutoff']:g}"
    if r["status"] == "challenger" and r["tune"]:
        cell += " (tuned)"
    if r["effective_from"] is not None:
        cell += f", from {r['effective_from']:%d %b %Y}"
    return cell


def action_cell(r: dict) -> str:
    if r["escalate_action"]:
        return f"{r['action']}; {r['escalate_action']} at {r['comparator']} {r['escalate_at']:g}"
    return r["action"]


def champion_cell(r: dict) -> str:
    return f"{r['comparator']} {r['champion_cutoff']:g}" if r["status"] == "champion" else "not running"


def window() -> dict:
    return _rows("select * from config.cfg_window")[0]


def strategy_metrics(period: str = "test") -> dict[str, dict]:
    rows = _rows("select * from backtest.bt_strategy_metrics where period = ?", [period])
    return {r["strategy_id"]: r for r in rows}


def bootstrap() -> dict[tuple[str, str], dict]:
    return {(r["strategy_id"], r["metric"]): r for r in _rows("select * from analysis.bootstrap_ci")}


def challenger_thresholds() -> list[dict]:
    return _rows("""
        select r.rule_id, r.status, r.tune, r.threshold as champion_cutoff,
               coalesce(t.challenger_cutoff, r.threshold) as challenger_cutoff, coalesce(t.is_kept, true) as is_kept,
               r.comparator, r.action, r.escalate_action, r.escalate_at, e.effective_from, e.detected_at
        from config.cfg_rules r
        left join backtest.bt_challenger_thresholds t using (rule_id)
        left join monitoring.mon_rule_effective_from e using (rule_id)
        order by cast(regexp_extract(r.rule_id, 'R(\\d+)', 1) as integer)""")


def sweep(period: str = "train") -> list[dict]:
    return _rows("""
        select m.*, s.status, s.is_configured_cutoff and s.status = 'champion' as is_champion_cutoff,
               coalesce(t.challenger_cutoff = m.cutoff, false)
                 or (s.status = 'challenger' and not r.tune and s.is_configured_cutoff) as is_challenger_cutoff,
               r.comparator
        from backtest.bt_sweep_metrics m
        join backtest.bt_sweep_strategies s using (strategy_id)
        join config.cfg_rules r on r.rule_id = m.rule_id
        left join backtest.bt_challenger_thresholds t on t.rule_id = m.rule_id
        where m.period = ?
        order by m.rule_id, m.cutoff""", [period])


def label_delay_gap() -> list[dict]:
    """For each tuned rule at its chosen cutoff: training months as measured at tuning time vs with all labels."""
    return _rows("""
        select t.rule_id, t.challenger_cutoff, k.cases as cases_known, f.cases as cases_all,
               k.loss_prevented as prevented_known, f.loss_prevented as prevented_all,
               k.precision as precision_known, f.precision as precision_all
        from backtest.bt_challenger_thresholds t
        join backtest.bt_sweep_strategies s on s.rule_id = t.rule_id and s.cutoff = t.challenger_cutoff
        join backtest.bt_sweep_metrics_known k on k.strategy_id = s.strategy_id and k.period = 'train'
        join backtest.bt_sweep_metrics f on f.strategy_id = s.strategy_id and f.period = 'train'
        order by t.rule_id""")


def weekly_series(series: str) -> list[dict]:
    return _rows("""
        select week, events, amount, unalerted_amount, baseline_mean, baseline_sd, is_alarm, week_closes_at
        from monitoring.mon_weekly_alarms where series = ? and week >= (select window_start from config.cfg_window)
        order by week""", [series])


def alarms() -> list[dict]:
    return _rows("""
        select series, week, events, baseline_mean, unalerted_amount, amount
        from monitoring.mon_weekly_alarms
        where is_alarm and week >= (select window_start from config.cfg_window)
        order by week, series""")


def credit_losses() -> dict[tuple[str, str], dict]:
    return {(r["strategy_id"], r["period"]): r for r in _rows("select * from backtest.bt_credit_losses")}


def rules_touching(typology: str, strategy: str = "challenger") -> list[dict]:
    """Which rules touched a fraud type's cases, and how many cases each (test and training months)."""
    return _rows("""
        with per_rule as (
            select c.period, c.case_id, unnest(string_split(g.rules, ',')) as rule_id
            from backtest.bt_strategy_graded g join backtest.bt_cases c using (case_id)
            where g.strategy_id = ? and c.typology = ?)
        select rule_id, count(distinct case_id) filter (where period = 'test') as test_cases,
               count(distinct case_id) filter (where period = 'train') as train_cases
        from per_rule group by rule_id order by test_cases desc, rule_id""", [strategy, typology])


def effective_dates() -> list[dict]:
    return _rows("select * from monitoring.mon_rule_effective_from")


def monthly_precision() -> list[dict]:
    return _rows("""
        select rule_id, cast(date_trunc('month', week) as date) as month, sum(alerts) as alerts,
               sum(fraud_alerts_known_at_maturity) / sum(alerts) as precision_at_maturity,
               sum(fraud_alerts_eventually) / sum(alerts) as precision_eventually
        from backtest.bt_monitoring_precision
        where week >= (select window_start from config.cfg_window)
        group by all order by rule_id, month""")


def overlap(strategy: str = "champion") -> list[dict]:
    return _rows("""
        select rule_id, period, cases_detected, cases_only_this_rule, loss_in_cases_only_this_rule
        from backtest.bt_rule_overlap where strategy_id = ? and period is not null
        order by cast(regexp_extract(rule_id, 'R(\\d+)', 1) as integer), period""", [strategy])


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


def typology_totals(strategy: str, period: str = "test") -> dict[str, dict]:
    """Outcomes per fraud type (variants summed), keyed by typology."""
    rows = _rows("""
        select typology, count(*) as cases, count(*) filter (where detected) as detected,
               sum(loss_if_uncaught) as loss, sum(loss_prevented) as prevented
        from backtest.bt_strategy_cases where strategy_id = ? and period = ?
        group by typology""", [strategy, period])
    return {r["typology"]: r for r in rows}


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
        ("Good applicants declined", num(ch["good_applicants_declined"]), num(cl["good_applicants_declined"])),
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
