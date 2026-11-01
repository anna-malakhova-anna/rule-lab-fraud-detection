"""The rule register (module F): docs/governance/rule-register.md. Every table is generated from config
(owners, change log) and the warehouse (inventory figures, quarterly reviews); edit those, not this file."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT, load_yaml

DOC = ROOT / "docs" / "governance" / "rule-register.md"

SHORT = {"keep": "keep", "retune": "retune", "retire candidate": "retire?", "investigate drift": "drift", "too early": "too early"}


def inventory_table() -> str:
    reviews = load_yaml("governance.yaml")["quarterly_review"]["reviews_without_added_value"]
    return R.markdown_table(
        ["Rule", "Owner", "Status", "Reason code", "Rationale", "Action", "Cutoff", "Last changed", "Precision (test)",
         "Alerts per day (test)", "Cases only it caught (test)", "Latest review", "Retirement trigger"],
        [(R.RULE_LABELS[r["rule_id"]], r["owner"], r["status"].replace("_", " "), f"`{r['reason_code']}`", r["rationale"],
          r["action"], f"{r['cutoff']:g}", f"{r['last_changed']:%Y-%m-%d} ({r['last_decision']})", R.pct(r["test_precision"], 1),
          R.num(r["test_alerts_per_day"], 1), "" if r["test_unique_cases"] is None else r["test_unique_cases"],
          r["latest_recommendation"] or "", R.retirement_trigger(r, reviews))
         for r in R.rule_inventory()])


def quarterly_matrix() -> str:
    rows = R.quarterly_review()
    quarters = sorted({r["quarter"] for r in rows})
    by_rule: dict[str, dict[str, str]] = {}
    for r in rows:
        by_rule.setdefault(r["rule_id"], {})[r["quarter"]] = SHORT[r["recommendation"]]
    return R.markdown_table(["Rule"] + [f"Review after {q}" for q in quarters],
                            [(R.RULE_LABELS[rid],) + tuple(cells[q] for q in quarters) for rid, cells in by_rule.items()])


def latest_review_table() -> str:
    rows = R.quarterly_review()
    latest = max(r["quarter"] for r in rows)
    return R.markdown_table(
        [f"Rule (review after {latest})", "Alerts judged", "Precision known", "Break-even precision", "Cases caught",
         "Cases only it caught", "Fraud $ it added (leave one out)", "Volume vs previous quarter", "Recommendation"],
        [(R.RULE_LABELS[r["rule_id"]] + (f" (alerts from {r['judged_quarter']})" if r["lag_quarters"] else ""),
          R.num(r["alerts"]), R.pct(r["precision_known"], 1), R.pct(r["break_even_precision"], 2), r["cases_caught"],
          r["unique_cases"], R.usd(r["added_value"]),
          "" if r["volume_vs_previous_quarter"] is None else f"{r['volume_vs_previous_quarter']:.2f}x", r["recommendation"])
         for r in rows if r["quarter"] == latest])


def change_log_table() -> str:
    return R.markdown_table(
        ["#", "Date", "Rule", "Change", "Cutoff after", "Action after", "Decision", "Backtest that justified it"],
        [(c["change_no"], f"{c['change_date']:%Y-%m-%d}", R.RULE_LABELS[c["rule_id"]], c["change"],
          "" if c["threshold"] is None else f"{c['threshold']:g}", c["action"] or "", c["decision"], c["backtest"])
         for c in R.rule_changes()])


def blocks() -> dict[str, str]:
    return {"gov-inventory": inventory_table(), "gov-latest-review": latest_review_table(),
            "gov-quarterly": quarterly_matrix(), "gov-change-log": change_log_table()}


def documents() -> dict[Path, dict[str, str]]:
    return {DOC: blocks()}
