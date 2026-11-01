"""The good-customer fast lane page (module E)."""
from __future__ import annotations

from scripts import results as R
from scripts.common import load_yaml
from scripts.sitegen.components import catbar, page_title, table


def _tradeoff(period: str) -> list[list]:
    return [[R.fast_lane_label(r["strategy_id"]), f'{r["good_holds_avoided"]:,}', f'{r["customer_hours_saved"]:,.0f}',
             f'{r["good_businesses_no_longer_held"]:,}', R.usd(r["fraud_let_through"]),
             "" if r["fraud_let_through_per_hold_avoided"] is None else R.usd(r["fraud_let_through_per_hold_avoided"])]
            for r in R.fast_lane_tradeoff(period) if r["strategy_id"] != "challenger"]


def fastlane() -> str:
    fl = load_yaml("rules.yaml")["fast_lane"]
    seg = [s for s in R.fast_lane_segments("fast_lane") if s["rule_id"] == "all"]
    est = next(s for s in seg if s["segment"] == "established, clean")
    rest = next(s for s in seg if s["segment"] != "established, clean")
    per_rule = [[R.RULE_LABELS[s["rule_id"]], s["segment"], f'{s["alerts"]:,}', R.pct(s["precision"], 1), f'{s["good_holds"]:,}']
                for s in R.fast_lane_segments("fast_lane") if s["rule_id"] != "all"]
    industries = [[s["segment"].replace("_", " "), f'{s["alerts"]:,}', s["alerts_on_fraud"], R.pct(s["precision"], 1)]
                  for s in R.fast_lane_segments("industry") if s["rule_id"] == "all"]
    trade = {r["strategy_id"]: r for r in R.fast_lane_tradeoff("test")}
    rec = trade[R.fast_lane_recommended()]
    rec_train = {r["strategy_id"]: r for r in R.fast_lane_tradeoff("train")}[R.fast_lane_recommended()]
    typ = [[R.fast_lane_label(r["strategy_id"]), R.TYPOLOGY_LABELS[r["typology"]], R.usd(r["fraud_let_through"])]
           for r in R.fast_lane_typologies() if r["fraud_let_through"] > 0.5]
    bars = [["never" if r["decline_at"] is None else f'{r["decline_at"]:g}' + (" (today)" if r["strategy_id"] == "decline_at:3" else ""),
             r["declined_by_r6"], r["good_applicants_declined"], r["fraud_applicants_declined"], R.pct(r["approval_rate"], 1),
             R.usd(r["fraud_let_through_vs_today"])] for r in R.decline_bar()]
    cap = f'${fl["recommended_max_amount"]:,}'
    rec_tile = (f'<div class="stat"><b>{rec["good_holds_avoided"]:,}</b><span>good customers\' holds avoided at the recommended '
                f'{cap} cap, with {R.usd(rec["fraud_let_through"])} of fraud let through (test months)</span></div>')
    return f"""{page_title("Fast lane", "Less friction for established, clean customers")}
{catbar([("#where", "Where alerts are false"), ("#tradeoff", "The trade-off"), ("#through", "What gets through"), ("#onboarding", "Onboarding")])}
<p>A business is in the fast lane while it has been open at least {fl["min_tenure_days"]} days and has had no returned
item in the last {fl["clean_days"]}. For those businesses, the rules aimed at a fraudster's own account
({", ".join(r.split("_")[0] for r in fl["softened_rules"])}) send a document request instead of a hold, on amounts
below a cap. Rules that protect a victim, and the credit rules, keep their action: established, clean businesses are
exactly who takeovers, payment redirection and bust-outs target.</p>
<div class="stats">
<div class="stat"><b>{R.pct(est["precision"], 1)}</b><span>of alerts on established, clean businesses were fraud (training months), against {R.pct(rest["precision"], 1)} for everyone else</span></div>
{rec_tile}
<div class="stat"><b>{R.usd(trade["fast_lane_clear_all"]["fraud_let_through"])}</b><span>let through if every alert on them were simply cleared</span></div>
</div>

<h2 id="where">Where the alerts are mostly false</h2>
<div class="card">{table(["Rule (training months)", "Segment", "Alerts", "Precision", "Good customers' holds"], per_rule, {2, 3, 4})}</div>
<details><summary>By industry (for discovery only: too few fraud cases per industry to set policy on)</summary>
<div class="card">{table(["Industry (training months)", "Alerts", "Of which fraud", "Precision"], industries, {1, 2, 3})}</div></details>

<h2 id="tradeoff">The trade-off, by cap</h2>
<p>The cap is swept, not tuned. Under the stated costs a hold is priced only by the money it ties up, so net value
can't choose it; the number to judge is the fraud let through for each hold avoided. The training months would have
pointed to a higher cap than the test months support.</p>
<p><b>Recommendation: a {cap} cap.</b> It let {R.usd(rec_train["fraud_let_through"])} of fraud through in the training months
and {R.usd(rec["fraud_let_through"])} in the test months, and spares {rec["good_businesses_no_longer_held"]:,} good businesses a hold.
It was chosen after seeing the test months, so that clean result isn't an independent check; the first quarterly review
after it ships is.</p>
<div class="card">{table(["Test months", "Good holds avoided", "Customer-hours saved", "Good businesses no longer held",
                         "Fraud $ let through", "Fraud $ per hold avoided"], _tradeoff("test"), {1, 2, 3, 4, 5})}</div>
<details><summary>The same on the training months</summary>
<div class="card">{table(["Training months", "Good holds avoided", "Customer-hours saved", "Good businesses no longer held",
                         "Fraud $ let through", "Fraud $ per hold avoided"], _tradeoff("train"), {1, 2, 3, 4, 5})}</div></details>
<p class="src">Source: backtest.bt_fast_lane_tradeoff. Write-up: docs/fastlane/fast-lane-review-DRAFT.md</p>

<h2 id="through">What gets through</h2>
<div class="card">{table(["Rule set (test months)", "Fraud type", "Fraud $ let through"], typ, {2})}</div>

<h2 id="onboarding">Onboarding: approval rate vs. fraud</h2>
<p>R6 declines an applicant who shares several identity details with earlier applicants and was incorporated only
weeks before. Raising that bar approves a few more applicants. The approval rate counts every application, including
those the bank's existing checks already decline, which dominate it.</p>
<div class="card">{table(["R6 declines at score (test months)", "Declined by R6", "Good applicants declined",
                         "Fraudulent applicants declined", "Approval rate", "Fraud $ let through vs today"], bars, {1, 2, 3, 4, 5})}</div>
<p class="src">Source: backtest.bt_onboarding_decline_bar</p>
"""
