"""The vendor bake-off page (module D). The vendors are invented."""
from __future__ import annotations

from scripts import results as R
from scripts.common import load_yaml
from scripts.sitegen.components import catbar, page_title, table


def vendors() -> str:
    cfg = load_yaml("vendors.yaml")["vendors"]
    profile = [[v["name"], v["kind"], ", ".join(cp.replace("_", " ") for cp in v["call_points"]), R.pct(v["coverage"]),
                f'{v["latency_ms"]:,} ms', f'${v["cost_per_call"]:.2f}'] for v in cfg.values()]
    decisions = [[d["vendor_name"], R.CALL_STRATEGY_LABELS[d["call_strategy"]], R.usd(d["net_value"]),
                  "yes" if d["fast_enough_for_payments"] else "no", "buy" if d["buy"] else "don't buy"] for d in R.vendor_decisions()]
    rows = [[r["vendor_name"], R.CALL_STRATEGY_LABELS[r["call_strategy"]], f'{r["calls"]:,}', R.usd(r["vendor_cost"]),
             R.usd(r["added_fraud_prevented"]), r["cases_only_with_vendor"], f'{r["added_good_businesses_flagged"]:,}',
             "n/a" if r["break_even_cost_per_call"] is None else f'${r["break_even_cost_per_call"]:.2f}', R.usd(r["net_value"])]
            for r in R.vendor_bakeoff()]
    return f"""{page_title("Vendors", "Buy or build: three invented data vendors")}
{catbar([("#decision", "Decision"), ("#comparison", "Full comparison"), ("#vendors", "The vendors")])}
<p>Each vendor answers at its call points with a risk score, or not at all when it doesn't cover the business. Its score
becomes a rule added to today's rules, and is graded three ways: calling it everywhere it can be called, only at
onboarding, or only when in-house signals already point at risk. Costs are calls times the price per call; false
positives are priced like any other good business flagged.</p>

<h2 id="decision">Decision</h2>
<div class="card">{table(["Vendor", "Best call strategy", "Net value (test months)", "Fast enough for payments", "Decision"], decisions, {2})}</div>

<h2 id="comparison">Full comparison (test months)</h2>
<p>"Cases only it caught" counts cases today's rules miss entirely. The vendors here mostly catch the same cases earlier,
which is worth dollars but adds no new cases. Calling only when already risky adds nothing, because those are exactly
the cases the rules already catch.</p>
<div class="card">{table(["Vendor", "Call strategy", "Calls", "Vendor cost", "Fraud $ added", "Cases only it caught",
                         "Extra good businesses flagged", "Break-even price per call", "Net value"], rows, {2, 3, 4, 5, 6, 7, 8})}</div>
<p class="src">Source: backtest.bt_vendor_bakeoff. Write-up: docs/vendors/vendor-bakeoff-DRAFT.md</p>

<h2 id="vendors">The vendors</h2>
<div class="card">{table(["Vendor", "What it is", "Called at", "Coverage", "Typical response time", "Price per call"], profile, {3, 4, 5})}</div>
"""
