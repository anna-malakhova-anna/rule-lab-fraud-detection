"""The monitoring page."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.charts import weekly_bars
from scripts.sitegen.components import catbar, page_title, table


def monitoring() -> str:
    alarms = [[f'{a["week"]:%Y-%m-%d}', a["series"].replace(":", " / ").replace("_", " "), a["events"], f'{a["baseline_mean"]:.1f}',
               R.usd(a["amount"])] for a in R.alarms()]
    ach = R.weekly_series("ach_debit_in:unauthorized")
    first_ach = next(w for w in ach if w["is_alarm"])
    credit = R.weekly_series("credit:payment_missed")
    gap = [[R.RULE_LABELS[g["rule_id"]], f'{g["cases_known"]} of {g["cases_all"]}', R.usd(g["prevented_known"]), R.usd(g["prevented_all"]),
            R.pct(g["precision_known"], 1), R.pct(g["precision_all"], 1)] for g in R.label_delay_gap()]
    w = R.window()
    prec = {}
    for m in R.monthly_precision():
        if m["month"] >= w["train_end"]:
            a = prec.setdefault(m["rule_id"], [0, 0.0, 0.0])
            a[0] += m["alerts"]; a[1] += m["precision_at_maturity"] * m["alerts"]; a[2] += m["precision_eventually"] * m["alerts"]
    prec_rows = [[R.RULE_LABELS[k], f'{v[0]:,}', R.pct(v[1] / v[0], 1), R.pct(v[2] / v[0], 1)] for k, v in sorted(prec.items())]
    return f"""{page_title("Monitoring", "What an analyst could see each week, without labels")}
{catbar([("#ach", "The month-12 pattern"), ("#credit", "Missed credit payments"), ("#labels", "Labels arrive late")])}
<p>Every week, each kind of returned payment (by rail and return reason) and each kind of credit event (missed
payments, charge-offs) is compared with its own previous 12 weeks. No fraud labels are involved: this is what an
analyst could see that week.</p>

<h2 id="ach">How the month-12 pattern was found</h2>
<p>Unauthorized returns on ACH debits had been near zero, then jumped. The first alarm became visible on
{first_ach["week_closes_at"]:%d %b %Y}. The investigation (docs/investigations/INV-001-ach-debit-returns.md, frozen at Phase 2)
led to R9, which now runs in the champion.</p>
{weekly_bars(ach, [(first_ach["week_closes_at"], "alarm visible")], "Unauthorized ACH-debit returns per week")}

<h2 id="credit">Missed payments on the line of credit</h2>
<p>Missed payments come from honest businesses that fail and from bust-outs. The "no champion alert" column in the
table view is the part no rule saw coming.</p>
{weekly_bars(credit, [], "Missed credit payments per week")}

<details><summary>Every alarm in the window (most are bursts of bad checks that the check rules already cover)</summary>
<div class="card">{table(["Week of", "Series", "Events", "Trailing mean", "Amount"], alarms, {2, 3, 4})}</div></details>
<p class="src">Source: monitoring.mon_weekly_alarms</p>

<h2 id="labels">Labels arrive late</h2>
<p>When tuning in month 12, the bank only knows the fraud it has confirmed so far. A bust-out is confirmed around
charge-off, about five months after the money leaves. The credit rules were tuned on what the bank could see at the time:</p>
<div class="card">{table(["Tuned rule (training months)", "Cases the bank knew of (all types)", "Prevented, as seen then", "Prevented, all labels", "Precision, as seen then", "Precision, all labels"], gap, {1, 2, 3, 4, 5})}</div>
<p>Weekly monitoring has the same lag. Precision in the test months, as known 30 days after each week vs eventually:</p>
<div class="card">{table(["Rule", "Alerts", "Precision at 30 days", "Precision eventually"], prec_rows, {1, 2, 3})}</div>
<p class="src">Source: backtest.bt_sweep_metrics_known, backtest.bt_monitoring_precision</p>
"""
