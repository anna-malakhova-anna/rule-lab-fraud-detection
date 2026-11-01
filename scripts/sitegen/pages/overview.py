"""The overview page."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.components import ICONS, table


def overview() -> str:
    t = R.totals()
    rules = R.challenger_thresholds()
    champ, chall = R.typology_totals("champion"), R.typology_totals("challenger")
    typ = [[label, champ[k]["cases"], champ[k]["detected"], chall[k]["detected"], R.usd(champ[k]["loss"]),
            R.usd(champ[k]["prevented"]), R.usd(chall[k]["prevented"])] for k, label in R.TYPOLOGY_LABELS.items() if k in champ]
    cl = R.credit_losses()
    ch, cc = cl.get(("champion", "test")), cl.get(("challenger", "test"))
    credit = [["Honest businesses that defaulted", ch["honest_defaults"], cc["honest_defaults"]],
              ["Balance when they missed a payment", R.usd(ch["balance_at_missed_payment"]), R.usd(cc["balance_at_missed_payment"])],
              ["Of which flagged by a rule in the 90 days before", R.usd(ch["balance_flagged_before_default"]), R.usd(cc["balance_flagged_before_default"])],
              ["Holds put on these struggling businesses", ch["holds_on_honest_defaulters"], cc["holds_on_honest_defaulters"]]]
    thresholds = [[R.RULE_LABELS[r["rule_id"]], R.action_cell(r), R.champion_cell(r), R.challenger_cell(r)] for r in rules]
    m = R.strategy_metrics("test")
    ch_m, cl_m = m["champion"], m["challenger"]
    return f"""<section class="hero">
<h1>Which rules should a small-business bank run?</h1>
<p>At what thresholds, and what does each change cost and save? Every rule here is graded on the three things a fraud
strategist actually trades off.</p>
<div class="features">
<div class="feature"><div class="icon">{ICONS["shield"]}</div><div><b>Fraud caught</b><span>Dollars prevented and cases detected</span></div></div>
<div class="feature"><div class="icon">{ICONS["people"]}</div><div><b>Good customers hurt</b><span>Businesses flagged, money held, payrolls delayed</span></div></div>
<div class="feature"><div class="icon">{ICONS["queue"]}</div><div><b>Review load</b><span>Reviews per day against a small team's capacity</span></div></div>
</div>
</section>

<div class="stats">
<div class="stat"><b>{R.pct(cl_m["dollar_recall"])}</b><span>of fraud dollars prevented by the challenger in the test months (champion: {R.pct(ch_m["dollar_recall"])})</span></div>
<div class="stat"><b>{cl_m["cases_detected"]} / {cl_m["cases"]}</b><span>fraud cases detected by the challenger (champion: {ch_m["cases_detected"]})</span></div>
<div class="stat"><b>{cl_m["good_businesses_flagged"]:,}</b><span>good businesses flagged by the challenger (champion: {ch_m["good_businesses_flagged"]:,})</span></div>
<div class="stat"><b>{cl_m["days_over_capacity"]} / {cl_m["business_days"]}</b><span>test-month days over review capacity (champion: {ch_m["days_over_capacity"]})</span></div>
</div>

<h2>Champion vs challenger, on months the tuning never saw</h2>
<p>The champion is what runs today: nine rules covering deposits, payments, onboarding, mules, account takeover and ACH
debits. The challenger adds three rules for the new line of credit. New cutoffs were tuned on the first 12 months
using only the fraud confirmed by then. Both rule sets are graded on months 13 to 18 ({t["test_cases"]} fraud cases).
Ranges are 90% bootstrap ranges over businesses.</p>
<div class="card">{table(["Test months", "Champion", "Challenger"], [list(r) for r in R.headline_rows()], {1, 2})}</div>
<p class="src">Source: backtest.bt_strategy_metrics, analysis.bootstrap_ci</p>

<h2>By fraud type (test months)</h2>
<div class="card">{table(["Fraud type", "Cases", "Detected: champion", "Detected: challenger", "Loss at stake", "Prevented: champion", "Prevented: challenger"], typ, {1, 2, 3, 4, 5, 6})}</div>
<p>One page per fraud type: <a href="types.html">Fraud types</a>.</p>

<h2>Credit losses that are not fraud (test months)</h2>
<p>Some honest businesses fail and default on their line. That's credit risk, not fraud, so it is never added to
fraud prevented. Holding a struggling customer's payments still counts as harm.</p>
<div class="card">{table(["", "Champion", "Challenger"], credit, {1, 2})}</div>
<p class="src">Source: backtest.bt_credit_losses</p>

<h2>Cutoffs</h2>
<div class="card">{table(["Rule", "Action", "Champion", "Challenger"], thresholds)}</div>
"""
