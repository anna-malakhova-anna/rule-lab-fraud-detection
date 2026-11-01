"""The vendor bake-off write-up (module D): docs/vendors/vendor-bakeoff-DRAFT.md. Vendors are invented.
Numbers and the buy / don't-buy line are generated; prose is a draft."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml

DOC = ROOT / "docs" / "vendors" / "vendor-bakeoff-DRAFT.md"


def blocks() -> dict[str, str]:
    rows, vendors = R.vendor_bakeoff(), load_yaml("vendors.yaml")["vendors"]
    table = R.markdown_table(
        ["Vendor", "Call strategy", "Calls", "Vendor cost", "Fraud $ added", "Cases only it caught", "Extra good businesses flagged",
         "Cost per $ prevented", "Break-even price per call", "Net value"],
        [(r["vendor_name"], R.CALL_STRATEGY_LABELS[r["call_strategy"]], R.num(r["calls"]), R.usd(r["vendor_cost"]),
          R.usd(r["added_fraud_prevented"]), r["cases_only_with_vendor"], R.num(r["added_good_businesses_flagged"]),
          "n/a" if r["cost_per_dollar_prevented"] is None else f"${r['cost_per_dollar_prevented']:.3f}",
          "n/a" if r["break_even_cost_per_call"] is None else f"${r['break_even_cost_per_call']:.2f}", R.usd(r["net_value"]))
         for r in rows])
    decisions = R.markdown_table(
        ["Vendor", "What it is", "Price per call", "Best call strategy", "Net value (test months)", "Fast enough for payments", "Decision"],
        [(d["vendor_name"], vendors[d["vendor"]]["kind"],
          f"${d['cost_per_call']:.2f}", R.CALL_STRATEGY_LABELS[d["call_strategy"]], R.usd(d["net_value"]),
          "yes" if d["fast_enough_for_payments"] else "no", "buy" if d["buy"] else "don't buy")
         for d in R.vendor_decisions()])
    return {"vendor-bakeoff": table, "vendor-decisions": decisions}


def documents() -> dict[Path, dict[str, str]]:
    return {DOC: blocks()}
