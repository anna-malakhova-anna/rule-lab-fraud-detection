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
    _write("cfg_window", ["window_start", "train_end", "window_end", "reviews_capacity_per_day", "bank_name"], [[
        start, add_months(start, w["train_months"]), add_months(start, w["months"]),
        cap["analysts"] * cap["reviews_per_analyst_day"], gen["bank_name"]]])
    mon = bt["monitoring"]
    _write("cfg_monitoring", ["baseline_weeks", "sigma", "min_count", "investigation_business_days", "precision_maturity_days"],
           [[mon["baseline_weeks"], mon["sigma"], mon["min_count"], mon["investigation_business_days"], mon["precision_maturity_days"]]])
    _write("cfg_rules", ["rule_id", "status", "tune", "effective_from_alarm", "action", "escalate_action", "escalate_at",
                         "comparator", "threshold", "score_description", "rationale"],
           [[rid, r["status"], bool(r.get("tune", False)), r.get("effective_from_alarm", ""), r["action"],
             r.get("escalate", {}).get("action", ""), r.get("escalate", {}).get("at", ""),
             r["comparator"], r["threshold"], r["score"], r["rationale"]] for rid, r in rules["rules"].items()])
    _write("cfg_rule_params", ["rule_id", "param", "value"],
           [[rid, k, v] for rid, r in rules["rules"].items() for k, v in r["params"].items()])
    _write("cfg_sweep", ["rule_id", "cutoff"], [[rid, c] for rid, r in rules["rules"].items() for c in r["sweep"]])
    _write("cfg_actions", ["action", "severity", "prevents", "hold_days", "is_review"],
           [[a, v["severity"], v["prevents"], v["hold_days"], v["review"]] for a, v in bt["actions"].items()])
    _write("cfg_costs", ["cost", "value"], [[k, v] for k, v in bt["costs"].items()])
    print(f"wrote seeds to {SEEDS}")


if __name__ == "__main__":
    main()
