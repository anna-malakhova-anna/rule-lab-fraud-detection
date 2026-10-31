"""Bootstrap ranges for champion vs challenger on the test months (ADR-005).

The test period holds only a few dozen fraud cases, so every headline number gets a 90% range. Resampling is
by business (a business carries its case and its false positives together). Written to analysis.bootstrap_ci.

  uv run python -m scripts.bootstrap
"""
from __future__ import annotations

import numpy as np

from scripts.common import connect, load_yaml

PER_BUSINESS = """
with cases as (
    select sc.strategy_id, c.business_id, sum(sc.loss_if_uncaught) as loss, sum(sc.loss_prevented) as prevented,
           count(*) as cases, count(*) filter (where detected) as detected
    from backtest.bt_strategy_cases as sc join backtest.bt_cases as c using (case_id)
    where sc.period = 'test' group by all
),
alerts as (
    select strategy_id, business_id, count(*) as alerts, count(*) filter (where label <> 'good') as fraud_alerts,
           max(case when label = 'good' then 1 else 0 end) as good_flagged,
           count(*) filter (where label = 'good' and hold_days > 0 and txn_type = 'payroll') as payrolls_delayed
    from backtest.bt_strategy_graded where period = 'test' group by all
),
grid as (select s.strategy_id, b.business_id from backtest.bt_strategies s cross join staging.stg_businesses b)
select g.strategy_id, g.business_id,
       coalesce(c.loss, 0) loss, coalesce(c.prevented, 0) prevented, coalesce(c.cases, 0) cases,
       coalesce(c.detected, 0) detected, coalesce(a.alerts, 0) alerts, coalesce(a.fraud_alerts, 0) fraud_alerts,
       coalesce(a.good_flagged, 0) good_flagged, coalesce(a.payrolls_delayed, 0) payrolls_delayed
from grid g
left join cases c using (strategy_id, business_id)
left join alerts a using (strategy_id, business_id)
order by g.strategy_id, g.business_id
"""

METRICS = {
    "dollar_recall": lambda d, w: (w * d["prevented"]).sum(-1) / (w * d["loss"]).sum(-1),
    "case_recall": lambda d, w: (w * d["detected"]).sum(-1) / (w * d["cases"]).sum(-1),
    "precision": lambda d, w: (w * d["fraud_alerts"]).sum(-1) / (w * d["alerts"]).sum(-1),
    "loss_prevented": lambda d, w: (w * d["prevented"]).sum(-1),
    "good_businesses_flagged": lambda d, w: (w * d["good_flagged"]).sum(-1),
    "payrolls_delayed": lambda d, w: (w * d["payrolls_delayed"]).sum(-1),
}


def main() -> None:
    cfg = load_yaml("backtest.yaml")["bootstrap"]
    con = connect(read_only=False)
    df = con.execute(PER_BUSINESS).fetchnumpy()
    strategies = sorted(set(df["strategy_id"]))
    n_biz = int((df["strategy_id"] == strategies[0]).sum())
    data = {s: {k: np.asarray(v[df["strategy_id"] == s], dtype=float) for k, v in df.items()
                if k not in ("strategy_id", "business_id")} for s in strategies}

    rng = np.random.default_rng(cfg["seed"])
    # Weight matrix: how many times each business is drawn in each replicate (same draws for both strategies,
    # so the champion-vs-challenger difference is paired).
    w = np.stack([np.bincount(rng.integers(0, n_biz, n_biz), minlength=n_biz) for _ in range(cfg["iterations"])])
    ones = np.ones((1, n_biz))
    rows = []
    for name, f in METRICS.items():
        reps = {}
        for s in strategies:
            reps[s] = f(data[s], w)
            point = float(f(data[s], ones)[0])
            lo, hi = np.nanpercentile(reps[s], [5, 95])
            rows.append((s, name, point, float(lo), float(hi)))
        if {"champion", "challenger"} <= set(reps):
            diff = reps["challenger"] - reps["champion"]
            point = float(f(data["challenger"], ones)[0] - f(data["champion"], ones)[0])
            lo, hi = np.nanpercentile(diff, [5, 95])
            rows.append(("challenger_minus_champion", name, point, float(lo), float(hi)))

    con.execute("create schema if not exists analysis")
    con.execute("create or replace table analysis.bootstrap_ci (strategy_id varchar, metric varchar, estimate double, p05 double, p95 double)")
    con.executemany("insert into analysis.bootstrap_ci values (?, ?, ?, ?, ?)", rows)
    con.close()
    for r in rows:
        print(f"{r[0]:<28} {r[1]:<24} {r[2]:>14,.3f}  [{r[3]:,.3f}, {r[4]:,.3f}]")


if __name__ == "__main__":
    main()
