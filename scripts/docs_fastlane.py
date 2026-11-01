"""The good-customer fast lane review (module E): docs/fastlane/fast-lane-review-DRAFT.md.
Numbers are generated; prose is a draft."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT

DOC = ROOT / "docs" / "fastlane" / "fast-lane-review-DRAFT.md"


def tradeoff_table(period: str) -> str:
    return R.markdown_table(
        [f"Rule set ({period} months)", "Good holds avoided", "Customer-hours of waiting saved", "Good businesses no longer held",
         "Fraud $ let through", "Fraud $ per hold avoided", "Net value change"],
        [(R.fast_lane_label(r["strategy_id"]), R.num(r["good_holds_avoided"]), R.num(r["customer_hours_saved"]),
          R.num(r["good_businesses_no_longer_held"]), R.usd(r["fraud_let_through"]),
          "" if r["fraud_let_through_per_hold_avoided"] is None else R.usd(r["fraud_let_through_per_hold_avoided"]),
          R.usd(r["net_value_change"]))
         for r in R.fast_lane_tradeoff(period) if r["strategy_id"] != "challenger"])


def segments_table(segment_type: str, header: str) -> str:
    return R.markdown_table(
        [header, "Rule", "Alerts", "Of which fraud", "Precision", "Good customers' holds"],
        [(s["segment"].replace("_", " "), "all rules" if s["rule_id"] == "all" else R.RULE_LABELS[s["rule_id"]],
          R.num(s["alerts"]), R.num(s["alerts_on_fraud"]), R.pct(s["precision"], 1), R.num(s["good_holds"]))
         for s in R.fast_lane_segments(segment_type) if segment_type == "fast_lane" or s["rule_id"] == "all"])


def typology_table() -> str:
    rows = [r for r in R.fast_lane_typologies() if r["fraud_let_through"] > 0.5]
    return R.markdown_table(["Rule set (test months)", "Fraud type", "Fraud $ let through"],
                            [(R.fast_lane_label(r["strategy_id"]), R.TYPOLOGY_LABELS[r["typology"]], R.usd(r["fraud_let_through"]))
                             for r in rows])


def decline_table() -> str:
    return R.markdown_table(
        ["R6 declines at score (test months)", "Applications", "Declined by R6", "Good applicants declined",
         "Fraudulent applicants declined", "Approval rate", "Fraud $ let through vs today", "Net value change vs today"],
        [("never" if r["decline_at"] is None else f"{r['decline_at']:g}" + (" (today)" if r["strategy_id"] == "decline_at:3" else ""),
          R.num(r["applications"]), r["declined_by_r6"], r["good_applicants_declined"], r["fraud_applicants_declined"],
          R.pct(r["approval_rate"], 1), R.usd(r["fraud_let_through_vs_today"]), R.usd(r["net_value_change_vs_today"]))
         for r in R.decline_bar()])


def blocks() -> dict[str, str]:
    return {
        "fast-lane-segments": segments_table("fast_lane", "Segment (training months)"),
        "fast-lane-industries": segments_table("industry", "Industry (training months)"),
        "fast-lane-tradeoff-test": tradeoff_table("test"),
        "fast-lane-tradeoff-train": tradeoff_table("train"),
        "fast-lane-typologies": typology_table(),
        "onboarding-decline-bar": decline_table(),
    }


def documents() -> dict[Path, dict[str, str]]:
    return {DOC: blocks()}
