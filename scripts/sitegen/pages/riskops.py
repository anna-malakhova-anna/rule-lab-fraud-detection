"""The Risk Ops page (module A): cases, prioritized vs first-in-first-out queues, SLA, and the feedback loop."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.charts import weekly_lines
from scripts.sitegen.components import catbar, page_title, table

POLICY_LABELS = {"priority": "Prioritized", "fifo": "First in, first out", "unlimited": "Unlimited reviewers (reference)"}


def riskops() -> str:
    w = R.window()
    q = R.queue_summary("test")
    days = R.queue_backlog_days("champion")
    rows = []
    for policy in ("priority", "fifo", "unlimited"):
        s = q[("champion", policy)]
        rows.append([POLICY_LABELS[policy], R.usd(s["fraud_prevented"]), f'{s["reviewed"]:,.0f}', f'{s["lapsed"]:,.0f}',
                     f'{s["good_holds_over_24h"]:,.0f}', f'{s["good_customer_hours_held"]:,.0f}',
                     f'{s["median_hours_to_decision_good"]:.1f} / {s["p90_hours_to_decision_good"]:.1f}',
                     f'{days[policy]["days_with_backlog"]} of {days[policy]["business_days"]}'])
    pr, ff = q[("champion", "priority")], q[("champion", "fifo")]

    backlog = R.queue_backlog("champion")
    series = [(POLICY_LABELS[p], [(b["week"], b["avg_backlog"],
                                   f'{POLICY_LABELS[p]}, week of {b["week"]:%d %b %Y}: {b["avg_backlog"]:.0f} cases waiting '
                                   f'at day end on average, {b["max_backlog"]} at most')
                                  for b in backlog if b["policy"] == p]) for p in ("priority", "fifo")]
    chart = weekly_lines(series, "Cases waiting at the end of the day, weekly average")

    both = []
    for strategy in ("champion", "challenger"):
        s = q[(strategy, "priority")]
        both.append([strategy.capitalize(), R.usd(s["fraud_prevented"]), f'{s["cases"]:,.0f}', f'{s["lapsed"]:,.0f}',
                     f'{s["good_holds_over_24h"]:,.0f}'])

    fb = [[R.RULE_LABELS[f["rule_id"]], f'{f["horizon_days"]} days', f'{f["cases"]:,}', R.pct(f["true_precision"], 1),
           R.pct(f["measured_precision"], 1), R.pct(f["labelled_share"])] for f in R.feedback_precision("champion")]
    return f"""{page_title("Risk Ops", "From alerts to decisions a small team can actually make")}
{catbar([("#queue", "Prioritized vs first-in-first-out"), ("#backlog", "Backlog"), ("#challenger", "With the credit rules"),
         ("#feedback", "Analyst labels")])}

<h2 id="queue">Same team, different order</h2>
<p>Every alert becomes a case: one per business per review day. Each case gets a priority score: what is at stake
(the payment, the application's stated revenue, or the credit line) times how often that rule's alerts turned out to
be fraud in the tuning months, as known at the time. Neither part reads the answer key. The team works
{w["reviews_capacity_per_day"]:g} cases per business day. A hold that nobody reviews within two business days lapses and
the money moves.</p>
<div class="stats">
<div class="stat"><b>{R.usd(pr["fraud_prevented"] - ff["fraud_prevented"])}</b><span>more fraud prevented in the test months by working the highest-priority cases first instead of the oldest</span></div>
<div class="stat"><b>{ff["good_holds_over_24h"] - pr["good_holds_over_24h"]:,.0f}</b><span>fewer good customers left waiting more than 24 hours on a hold</span></div>
</div>
<div class="card">{table(["Order (champion, test months)", "Fraud $ prevented", "Cases reviewed", "Cases that lapsed",
                         "Good customers held > 24h", "Good-customer hours held", "Hours to decision, median / p90",
                         "Days ending with a backlog"], rows, {1, 2, 3, 4, 5, 6, 7})}</div>
<p class="src">Source: analysis.queue_summary (scripts/queue_sim.py over backtest.ops_cases)</p>

<h2 id="backlog">Backlog</h2>
<p>Either way, the queue backs up in the spring peak. Prioritizing doesn't make the backlog smaller; it changes who waits.</p>
<div class="card">{chart}</div>
<p class="src">Source: analysis.queue_daily</p>

<h2 id="challenger">With the credit rules added (prioritized queue)</h2>
<div class="card">{table(["Rule set", "Fraud $ prevented", "Cases", "Cases that lapsed", "Good customers held > 24h"], both, {1, 2, 3, 4})}</div>

<h2 id="feedback">Analyst decisions become labels</h2>
<p>Reviewed cases are labelled on the day of the decision, with error: analysts clear 10% of fraud cases by mistake
and mark 2% of good ones as fraud. Cases nobody reviewed are labelled only when the fraud is confirmed some other way.
For noisy rules, analyst error inflates measured precision far more than label delay deflates it.</p>
<div class="card">{table(["Rule (champion, test months)", "Known after", "Cases", "True precision", "Measured precision",
                         "Share labelled"], fb, {2, 3, 4, 5})}</div>
<p class="src">Source: analysis.feedback_precision. Playbooks for each rule: docs/playbooks/.</p>
"""
