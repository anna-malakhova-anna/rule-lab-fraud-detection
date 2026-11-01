"""Export the YAML config to dbt seeds (dbt/seeds/cfg_*.csv). YAML is the source of truth; seeds are generated.

  uv run python -m scripts.export_config
"""
from __future__ import annotations

import csv
import datetime as dt

from scripts.common import ROOT, load_yaml

SEEDS = ROOT / "dbt" / "seeds"


def _write(name: str, header: list[str], rows: list[list]) -> None:
    with (SEEDS / f"{name}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main() -> None:
    gen, rules, bt = load_yaml("generation.yaml"), load_yaml("rules.yaml"), load_yaml("backtest.yaml")
    w = gen["window"]
    start = dt.date.fromisoformat(w["start_date"])

    def add_months(d: dt.date, m: int) -> dt.date:
        y, mm = divmod(d.month - 1 + m, 12)
        return dt.date(d.year + y, mm + 1, 1)

    cap = bt["capacity"]
    _write("cfg_window", ["window_start", "train_end", "window_end", "reviews_capacity_per_day", "bank_name",
                          "instant_launch_date"], [[
        start, add_months(start, w["train_months"]), add_months(start, w["months"]),
        cap["analysts"] * cap["reviews_per_analyst_day"], gen["bank_name"], gen["instant_payouts"]["launch_date"]]])
    ops = bt["ops"]
    flat = {f"review_window_{k}": v for k, v in ops["review_window_business_days"].items()}
    flat.update({k: v for k, v in ops.items() if k != "review_window_business_days"})
    _write("cfg_ops", ["param", "value"], [[k, v] for k, v in flat.items()])
    vend = load_yaml("vendors.yaml")
    _write("cfg_vendors", ["vendor", "rule_id", "vendor_name", "kind", "cost_per_call", "latency_ms", "coverage"],
           [[k, v["rule_id"], v["name"], v["kind"], v["cost_per_call"], v["latency_ms"], v["coverage"]]
            for k, v in vend["vendors"].items()])
    _write("cfg_latency_budget", ["decision_point", "budget_ms"], [[k, v] for k, v in vend["latency_budget_ms"].items()])
    mon = bt["monitoring"]
    _write("cfg_monitoring", ["baseline_weeks", "sigma", "min_count", "investigation_business_days", "precision_maturity_days"],
           [[mon["baseline_weeks"], mon["sigma"], mon["min_count"], mon["investigation_business_days"], mon["precision_maturity_days"]]])
    _write("cfg_rules", ["rule_id", "reason_code", "owner", "status", "tune", "effective_from_alarm", "action", "escalate_action",
                         "escalate_at", "comparator", "threshold", "score_description", "rationale"],
           [[rid, r["reason_code"], r["owner"], r["status"], bool(r.get("tune", False)), r.get("effective_from_alarm", ""), r["action"],
             r.get("escalate", {}).get("action", ""), r.get("escalate", {}).get("at", ""),
             r["comparator"], r["threshold"], r["score"], r["rationale"]] for rid, r in rules["rules"].items()])
    fl = rules["fast_lane"]
    _write("cfg_fast_lane", ["min_tenure_days", "clean_days", "soften_to"],
           [[fl["min_tenure_days"], fl["clean_days"], fl["soften_to"]]])
    _write("cfg_fast_lane_rules", ["rule_id"], [[rid] for rid in fl["softened_rules"]])
    _write("cfg_fast_lane_caps", ["max_amount"], [["" if c == "none" else c] for c in fl["max_amount_sweep"]])
    # `never` declines nobody: an empty cutoff.
    _write("cfg_decline_bar", ["decline_at"], [["" if d == "never" else d] for d in rules["decline_bar_sweep"]])
    gov = load_yaml("governance.yaml")
    _write("cfg_governance", ["param", "value"], [[k, v] for k, v in gov["quarterly_review"].items()])
    _write("cfg_review_lag", ["rule_id", "lag_quarters"],
           [[rid, gov["lag_quarters"].get(rid, 0)] for rid, r in rules["rules"].items() if r["status"] in ("champion", "challenger")])
    _write("cfg_rule_changes", ["change_no", "change_date", "rule_id", "change", "threshold", "action", "decision", "backtest"],
           [[i + 1, c["date"], c["rule_id"], c["change"], c.get("threshold", ""), c.get("action", ""), c["decision"], c["backtest"]]
            for i, c in enumerate(load_yaml("rule_changes.yaml")["changes"])])
    _write("cfg_rule_params", ["rule_id", "param", "value"],
           [[rid, k, v] for rid, r in rules["rules"].items() for k, v in r["params"].items()])
    _write("cfg_sweep", ["rule_id", "cutoff"], [[rid, c] for rid, r in rules["rules"].items() for c in r["sweep"]])
    _write("cfg_actions", ["action", "severity", "prevents", "hold_days", "is_review"],
           [[a, v["severity"], v["prevents"], v["hold_days"], v["review"]] for a, v in bt["actions"].items()])
    _write("cfg_costs", ["cost", "value"], [[k, v] for k, v in bt["costs"].items()])
    print(f"wrote seeds to {SEEDS}")


if __name__ == "__main__":
    main()
