"""The Risk Ops queue: ordering, capacity, lapsing and grading, on a tiny hand-made queue."""
import datetime as dt

from scripts.queue_sim import grade, simulate

D = [dt.date(2026, 1, 5) + dt.timedelta(days=i) for i in range(5)]          # Mon..Fri
WINDOWS = {"hold": 2, "rfi": 5, "block": 2}


def case(day, hour, action, priority, is_fraud=False, fraud_case=None, business=1):
    # (strategy, period, business, review_date, opened_at, action, priority, is_fraud, fraud_case_id, payroll, rules)
    return ("champion", "test", business, D[day], dt.datetime.combine(D[day], dt.time(hour)), action, priority,
            is_fraud, fraud_case, False, ["R1"])


def test_priority_works_the_valuable_case_first_and_fifo_the_oldest():
    cases = [case(0, 8, "hold", 1, business=1), case(0, 9, "hold", 100, business=2)]
    pri, _ = simulate(cases, D, 1, "priority", WINDOWS, 13)
    fifo, _ = simulate(cases, D, 1, "fifo", WINDOWS, 13)
    assert pri[1]["decided_at"].date() == D[0] and pri[0]["decided_at"].date() == D[1]
    assert fifo[0]["decided_at"].date() == D[0] and fifo[1]["decided_at"].date() == D[1]


def test_unreviewed_hold_lapses_after_its_window():
    cases = [case(0, 8, "hold", 100, business=1), case(0, 8, "hold", 50, business=2), case(0, 8, "hold", 10, business=3)]
    out, per_day = simulate(cases, D, 1, "priority", WINDOWS, 13)
    assert [o["reviewed"] for o in out] == [True, True, False]       # capacity 1/day, window 2 days
    assert out[2]["lapsed_day"] == D[2]
    assert [d["worked"] for d in per_day[:3]] == [1, 1, 0]


def test_unlimited_reviews_everything_on_arrival():
    cases = [case(0, 8, "hold", i, business=i) for i in range(10)]
    out, per_day = simulate(cases, D, 1, "unlimited", WINDOWS, 13)
    assert all(o["reviewed"] and o["decided_at"].date() == D[0] for o in out)
    assert per_day[0]["backlog"] == 0


def test_grading_credits_only_reviewed_cases_and_rfi_timing():
    t_loss = dt.datetime.combine(D[1], dt.time(10))
    losses = {7: [(t_loss, 1000.0)]}
    hold = [case(0, 8, "hold", 1, is_fraud=True, fraud_case=7)]
    assert grade(hold, [{"reviewed": True, "decided_at": dt.datetime.combine(D[1], dt.time(13))}], losses, 13)["fraud_prevented"] == 1000
    assert grade(hold, [{"reviewed": False, "lapsed_day": D[2]}], losses, 13)["fraud_prevented"] == 0
    rfi = [case(0, 8, "rfi", 1, is_fraud=True, fraud_case=7)]
    # An RFI decided after the money left prevents nothing; decided before, half (ADR-003).
    assert grade(rfi, [{"reviewed": True, "decided_at": dt.datetime.combine(D[1], dt.time(13))}], losses, 13)["fraud_prevented"] == 0
    assert grade(rfi, [{"reviewed": True, "decided_at": dt.datetime.combine(D[0], dt.time(13))}], losses, 13)["fraud_prevented"] == 500


def test_warehouse_queue_is_consistent(con):
    rows = con.execute("select strategy_id, policy, period, cases, reviewed, lapsed, fraud_prevented from analysis.queue_summary").fetchall()
    by = {(s, p, per): (c, r, lap, f) for s, p, per, c, r, lap, f in rows}
    for (s, p, per), (c, r, lap, f) in by.items():
        assert r + lap == c
        assert f <= by[(s, "unlimited", per)][3] + 0.01, "a capacity-limited queue cannot beat unlimited reviewers"
