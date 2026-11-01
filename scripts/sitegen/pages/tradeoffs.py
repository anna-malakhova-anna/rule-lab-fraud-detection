"""The tradeoffs page."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.charts import reviews_chart, tradeoff_panel
from scripts.sitegen.components import catbar, page_title, table


def tradeoffs() -> str:
    w = R.window()
    sweep = R.sweep("train")
    panels = "".join(tradeoff_panel(rid, [p for p in sweep if p["rule_id"] == rid]) for rid in R.RULE_LABELS)
    overlap = [[R.RULE_LABELS[o["rule_id"]], o["cases_detected"], o["cases_only_this_rule"]]
               for o in R.overlap("challenger") if o["period"] == "test"]
    harm = [[h["archetype"].replace("_", " "), f'{h["good_alerts"]:,}', R.usd(h["dollar_days"])] for h in R.harm_by_archetype("challenger")]
    return f"""{page_title("Trade-offs", "Every cutoff, what it catches and who it hurts")}
{catbar([("#curves", "Cutoff curves"), ("#capacity", "Review load"), ("#overlap", "Overlap"), ("#harm", "Who gets flagged")])}
<h2 id="curves">Each rule's cutoffs (tuning months)</h2>
<p>Each dot is one cutoff. Moving right flags more good businesses; moving up prevents more fraud. A curve that flattens
early means looser cutoffs only add friction. Hover a dot for reviews per day.</p>
<div class="grid">{panels}</div>
<p class="src">Source: backtest.bt_sweep_metrics (period = train, all labels)</p>

<h2 id="capacity">Review load against capacity</h2>
<p>Each alert is a review on the next business day, with at most one review per business per day. Capacity is
{w["reviews_capacity_per_day"]:g} reviews per business day (2.25 analysts for 12,000 businesses).</p>
{reviews_chart(R.weekly_reviews())}

<h2 id="overlap">Which rules earn their alerts (challenger, test months)</h2>
<p>A case "only this rule touched" would be missed if the rule were turned off.</p>
<div class="card">{table(["Rule", "Cases touched", "Cases only this rule touched"], overlap, {1, 2})}</div>

<h2 id="harm">Who the false positives are (challenger, test months)</h2>
<p>Good businesses grouped by the hidden archetype the generator gave them. The bank cannot see these labels; the backtest can.</p>
<div class="card">{table(["Kind of business", "Alerts on good businesses", "Dollar-days held"], harm, {1, 2})}</div>
"""
