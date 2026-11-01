"""Risk Ops queue simulation (module A, ADR-019).

Cases (backtest.ops_cases) arrive on their review day. Each business day the team works up to its capacity:
  fifo       oldest case first
  priority   highest priority (expected loss x likelihood) first; ties go to the oldest
  unlimited  every case reviewed the day it arrives (the backtest's implicit assumption, for reference)
A case not reviewed within its action's window lapses: an unreviewed hold auto-releases, an RFI goes stale.

Grading (here, after the simulation, from the answer key via backtest tables):
  fraud prevented  a loss transaction is stopped by a REVIEWED case on the same fraud case: fully by a hold or
                   block raised before it, half (ADR-003) by an RFI sent before it.
  good customers   waiting time from alert to decision (or to the hold lapsing); holds over 24 hours.
  backlog          cases waiting at the end of each day.

The feedback loop: analysts' decisions on reviewed cases become labels on the decision day, with error. Measured
precision per rule, as known 7/30/90 days after the alert, is compared with the truth.

Small Python because a queue carrying a backlog from day to day is awkward in SQL. Writes analysis.queue_*.

  uv run python -m scripts.queue_sim
"""
from __future__ import annotations

import datetime as dt
import heapq
from collections import defaultdict

import numpy as np

from scripts.common import connect, load_yaml

POLICIES = ("fifo", "priority", "unlimited")
HORIZONS = (7, 30, 90)


def _load(con) -> dict:
    cases = con.execute("""
        select strategy_id, period, business_id, review_date, opened_at, action, priority, is_fraud,
               fraud_case_id, holds_payroll, rule_list
        from backtest.ops_cases
        where review_date in (select business_date from backtest.bt_business_days)
        order by strategy_id, review_date, opened_at, business_id""").fetchall()
    days = [r[0] for r in con.execute("select business_date from backtest.bt_business_days order by 1").fetchall()]
    losses = defaultdict(list)
    for case_id, t, amt in con.execute("select case_id, txn_time, loss_amount from backtest.bt_loss_txns").fetchall():
        losses[case_id].append((t, amt))
    known = dict(con.execute("select case_id, label_known_at from backtest.bt_cases").fetchall())
    capacity = con.execute("select reviews_capacity_per_day from config.cfg_window").fetchone()[0]
    return {"cases": cases, "days": days, "losses": losses, "known": known, "capacity": int(capacity)}


def simulate(cases: list[tuple], days: list[dt.date], capacity: int, policy: str, windows: dict,
             hour: int) -> tuple[list[dict], list[dict]]:
    """Work the queue day by day. Returns (one outcome per case, one row per business day).

    A case outcome is {"reviewed": True, "decided_at": datetime} or {"reviewed": False, "lapsed_day": date}.
    """
    day_index = {d: i for i, d in enumerate(days)}
    arrivals = defaultdict(list)
    for i, c in enumerate(cases):
        arrivals[day_index[c[3]]].append(i)
    deadline = [day_index[c[3]] + windows[c[5]] - 1 for c in cases]     # last business day a case can be worked
    outcomes: list[dict | None] = [None] * len(cases)
    per_day: list[dict] = []
    queue: list[tuple] = []                                            # heap of (sort key, case index)

    def lapse(i: int, di: int) -> None:
        outcomes[i] = {"reviewed": False, "lapsed_day": days[min(di, len(days) - 1)]}

    for di, day in enumerate(days):
        for i in arrivals.get(di, []):
            c = cases[i]
            key = (-c[6], c[4], c[2]) if policy == "priority" else (c[4], c[2])
            heapq.heappush(queue, (key, i))
        limit = len(queue) if policy == "unlimited" else capacity
        worked, waiting = 0, []
        while queue and worked < limit:
            _, i = heapq.heappop(queue)
            outcomes[i] = {"reviewed": True, "decided_at": dt.datetime.combine(day, dt.time(hour))}
            worked += 1
        # Whatever is left either lapses tonight (its window ends today) or waits for tomorrow.
        for item in queue:
            if di >= deadline[item[1]]:
                lapse(item[1], di + 1)
            else:
                waiting.append(item)
        queue = waiting
        heapq.heapify(queue)
        per_day.append({"business_date": day, "worked": worked, "backlog": len(queue)})
    for _, i in queue:                                                 # still waiting when the window closes
        lapse(i, len(days))
    return outcomes, per_day


def grade(cases, outcomes, losses, hour) -> dict:
    """Fraud prevented, good-customer waiting and backlog for one policy and rule set."""
    by_fraud_case = defaultdict(list)
    good_waits, payroll_waits = [], 0
    reviewed = lapsed = 0
    for c, o in zip(cases, outcomes):
        if o["reviewed"]:
            reviewed += 1
        else:
            lapsed += 1
        opened = c[4]
        if c[7] and c[8] is not None and o["reviewed"]:
            by_fraud_case[c[8]].append((c[5], opened, o["decided_at"]))
        if not c[7]:
            end = o["decided_at"] if o["reviewed"] else dt.datetime.combine(o["lapsed_day"], dt.time(hour))
            hours = max(0.0, (end - opened).total_seconds() / 3600)
            if c[5] in ("hold", "block"):
                good_waits.append(hours)
                payroll_waits += bool(c[9]) and hours > 24
    prevented = 0.0
    for case_id, acts in by_fraud_case.items():
        for t, amt in losses.get(case_id, []):
            factor = 0.0
            for action, opened, decided in acts:
                if action in ("hold", "block") and opened <= t:
                    factor = 1.0
                elif action == "rfi" and decided <= t:
                    factor = max(factor, 0.5)
            prevented += amt * factor
    gw = np.array(good_waits) if good_waits else np.zeros(1)
    return {"cases": len(cases), "reviewed": reviewed, "lapsed": lapsed, "fraud_prevented": prevented,
            "good_holds": len(good_waits), "good_holds_over_24h": int((gw > 24).sum()) if good_waits else 0,
            "good_customer_hours_held": float(gw.sum()) if good_waits else 0.0,
            "median_hours_to_decision_good": float(np.median(gw)) if good_waits else 0.0,
            "p90_hours_to_decision_good": float(np.percentile(gw, 90)) if good_waits else 0.0,
            "payroll_holds_over_24h": payroll_waits}


def feedback(cases, outcomes, known, cfg, period: str) -> list[tuple]:
    """Measured precision per rule from analyst labels (with error) and confirmed fraud, at each horizon."""
    rng = np.random.default_rng(cfg["seed"])
    rows, per_rule = [], defaultdict(list)
    for c, o in zip(cases, outcomes):
        if c[1] != period:
            continue
        analyst = None
        if o["reviewed"]:
            says_fraud = (rng.random() >= cfg["analyst_miss_rate"]) if c[7] else (rng.random() < cfg["analyst_false_flag_rate"])
            analyst = (o["decided_at"], says_fraud)
        confirmed = known.get(c[8]) if c[7] else None
        for rule in c[10]:
            per_rule[rule].append((c[4], c[7], analyst, confirmed))
    for rule, items in sorted(per_rule.items()):
        truth = sum(1 for i in items if i[1]) / len(items)
        for h in HORIZONS:
            labelled = flagged = 0
            for opened, _is_fraud, analyst, confirmed in items:
                cutoff = opened + dt.timedelta(days=h)
                says = None
                if analyst and analyst[0] <= cutoff:
                    says = analyst[1]
                if confirmed is not None and confirmed <= cutoff:
                    says = True                         # a confirmed loss overrides a cleared case
                if says is not None:
                    labelled += 1
                    flagged += says
            # Banks usually count an unlabelled alert as "not fraud", which understates precision early on.
            rows.append((rule, h, len(items), truth, flagged / len(items), labelled / len(items)))
    return rows


def main() -> None:
    ops = load_yaml("backtest.yaml")["ops"]
    windows = ops["review_window_business_days"]
    con = connect(read_only=False)
    data = _load(con)
    summary, daily, fb = [], [], []
    for strategy in ("champion", "challenger"):
        cases = [c for c in data["cases"] if c[0] == strategy]
        for policy in POLICIES:
            per_case, per_day = simulate(cases, data["days"], data["capacity"], policy, windows, ops["decision_hour"])
            for period in ("train", "test"):
                idx = [i for i, c in enumerate(cases) if c[1] == period]
                g = grade([cases[i] for i in idx], [per_case[i] for i in idx], data["losses"], ops["decision_hour"])
                summary.append((strategy, policy, period, *g.values()))
            for d in per_day:
                daily.append((strategy, policy, d["business_date"], d["worked"], d["backlog"]))
            if policy == "priority":
                fb += [(strategy, *r) for r in feedback(cases, per_case, data["known"], ops, "test")]
    keys = list(grade([], [], {}, 13).keys())
    con.execute("create schema if not exists analysis")
    con.execute("create or replace table analysis.queue_summary (strategy_id varchar, policy varchar, period varchar, "
                + ", ".join(f"{k} double" for k in keys) + ")")
    con.executemany(f"insert into analysis.queue_summary values ({', '.join('?' * (3 + len(keys)))})", summary)
    con.execute("create or replace table analysis.queue_daily (strategy_id varchar, policy varchar, business_date date, "
                "reviewed integer, backlog integer)")
    con.executemany("insert into analysis.queue_daily values (?, ?, ?, ?, ?)", daily)
    con.execute("create or replace table analysis.feedback_precision (strategy_id varchar, rule_id varchar, horizon_days integer, "
                "cases integer, true_precision double, measured_precision double, labelled_share double)")
    con.executemany("insert into analysis.feedback_precision values (?, ?, ?, ?, ?, ?, ?)", fb)
    for r in con.execute("""select strategy_id, policy, round(fraud_prevented), reviewed, lapsed, good_holds_over_24h,
                                   round(median_hours_to_decision_good, 1)
                            from analysis.queue_summary where period = 'test' order by 1, 2""").fetchall():
        print(r)
    con.close()


if __name__ == "__main__":
    main()
