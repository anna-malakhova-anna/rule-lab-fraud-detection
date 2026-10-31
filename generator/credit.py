"""The revolving line of credit, and the two ways a line ends in loss (ADR-016).

Policy (config/generation.yaml `credit`): a business becomes eligible after six months of history, about a third
take a line, and the limit is half of the account's average monthly inflow over the 90 days before opening.
Draws land in the operating account (`loc_draw`) and repayments leave it (`loc_repayment`). Line events (opened,
increase requested and granted, payment missed, charged off) go to raw `credit_line_events`.

Two endings that both look like "drew the line, then defaulted":

  credit_bust_out (FRAUD, typology): months of clean use, then a few weeks of round-trip money pumped through the
      account so its inflows look bigger, a limit increase the policy grants on those inflows, then the whole line
      drawn and wired out within hours. Loss = the drawn money sent out.

  failing_business (NOT fraud, archetype): revenue falls away over two to five months, the owner draws the line to
      keep paying staff and suppliers, then the business stops and the line is charged off. A credit loss, graded
      separately and never counted as fraud prevented.
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, INBOUND, Calendar, times_on
from generator.legit import Payees
from generator.world import Business

LINE_EVENT_TYPES = ("line_opened", "limit_increase_requested", "limit_increased", "payment_missed", "charged_off")


def _add(tx: dict, rows: dict) -> dict:
    n = len(rows["t"])
    fill = {"counterparty_id": -1, "payee_id": -1, "return_after_s": -1, "return_reason": "", "case_id": -1,
            "role": "", "loss_amount": 0.0}
    for c in tx:
        add = rows.get(c, fill.get(c))
        arr = np.asarray(add, dtype=object if tx[c].dtype == object else tx[c].dtype) if np.ndim(add) else \
            np.full(n, add, dtype=object if tx[c].dtype == object else tx[c].dtype)
        tx[c] = np.concatenate([tx[c], arr])
    return tx


def _monthly_inflow(tx: dict, t_end: int) -> float:
    """What the bank's policy sees: average monthly inflow over the 90 days before t_end (no internal transfers)."""
    inbound = np.isin(tx["txn_type"], list(INBOUND - {"internal_transfer_in", "loc_draw"}))
    m = inbound & (tx["t"] >= t_end - 90 * DAY) & (tx["t"] < t_end)
    return float(tx["amount"][m].sum()) / 90 * 30.4


def run(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, tx: dict, payees: Payees,
        lines: list, events: list, ctx: dict, case_id: int | None) -> tuple[dict, dict | None]:
    c = cfg["credit"]
    lo, hi = ctx["lo"], ctx["hi"]
    bust = b.fraud == "credit_bust_out"
    if not bust:
        if b.fraud or hi - lo < c["min_history_days"] + 90 or rng.random() >= c["take_up"]:
            return tx, None
        open_day = int(rng.uniform(lo + c["min_history_days"], hi - 60))
    else:
        t = cfg["typologies"]["credit_bust_out"]
        ramp_day = b.extra["case_day"]
        open_day = max(lo + 90, ramp_day - int(rng.uniform(*t["line_before_ramp_days"])))
    bid, op = b.business_id, b.business_id * 10
    open_t = int(open_day * DAY + 10 * HOUR)
    limit = float(np.clip(round(_monthly_inflow(tx, open_t) * c["limit_share_of_monthly_inflow"], -3), c["limit_min"], c["limit_cap"]))
    lines.append({"line_id": bid, "business_id": bid, "opened_t": open_t, "initial_limit": limit})
    events.append((bid, open_t, "line_opened", limit, 0.0))

    failing = (not bust) and hi - open_day > 200 and rng.random() < c["failing_share"]
    if failing:
        b.archetype = "failing_business"
        fail_day = int(rng.uniform(open_day + 150, min(hi, cal.n_days) - 5))
        decline = int(rng.uniform(*c["failing_decline_days"]))
        # Revenue falls away: inflows thin out towards the failure date, then everything stops.
        ramp = np.clip((tx["t"] - (fail_day - decline) * DAY) / (decline * DAY), 0, 1)
        inbound = np.isin(tx["txn_type"], list(INBOUND - {"internal_transfer_in"}))
        keep = ~(inbound & (rng.random(len(ramp)) < 0.85 * ramp)) & (tx["t"] < fail_day * DAY)
        tx = {k: v[keep] for k, v in tx.items()}
        end_day = fail_day
    elif bust:
        end_day = ramp_day
    else:
        end_day = hi

    # Monthly use: draws now and then, repaid over the following months.
    balance, draws_t, draws_a, reps_t, reps_a = 0.0, [], [], [], []
    for start in range(open_day + 3, end_day, 30):
        in_distress = failing and start >= fail_day - decline
        if in_distress:
            amt = (limit - balance) * rng.uniform(0.3, 0.7)          # drawn to keep paying staff and suppliers
        elif rng.random() < c["draw_prob_per_month"]:
            amt = min(limit - balance, limit * rng.uniform(*c["draw_share_of_limit"]))
        else:
            amt = 0.0
        if amt >= 100:
            draws_t.append(int(times_on(rng, np.array([start]))[0]))
            draws_a.append(round(amt, 2))
            balance += round(amt, 2)
        due = start + 28
        if balance > 0 and due < end_day:
            pay = balance * (0.03 if in_distress else rng.uniform(*c["repay_share_of_balance"]))
            reps_t.append(int(times_on(rng, np.array([due]))[0]))
            reps_a.append(round(pay, 2))
            balance -= round(pay, 2)

    # One limit increase for some honest lines; seasonal businesses ask in early spring, ahead of their peak.
    if not bust and not failing and rng.random() < c["increase_request_share"]:
        if b.archetype == "seasonal_heavy":
            days = cal.days(open_day + 30, end_day)
            march = days[cal.at(cal.month, days) == 2]
            req_day = int(rng.choice(march)) if len(march) else None
        else:
            req_day = int(rng.uniform(open_day + 60, end_day)) if end_day - open_day > 90 else None
        if req_day is not None:
            t_req = int(req_day * DAY + 11 * HOUR)
            new_limit = min(c["limit_cap"], round(limit * c["increase_multiple"], -3))
            events.append((bid, t_req, "limit_increase_requested", limit, None))
            events.append((bid, t_req + DAY, "limit_increased", new_limit, None))

    if draws_t:
        tx = _add(tx, {"business_id": bid, "account_id": op, "t": draws_t, "txn_type": "loc_draw", "amount": draws_a,
                       "counterparty_id": 2})
    if reps_t:
        tx = _add(tx, {"business_id": bid, "account_id": op, "t": reps_t, "txn_type": "loc_repayment", "amount": reps_a})

    case = None
    if failing:
        _default(c, cal, events, bid, fail_day * DAY, balance)
    if bust:
        tx, case, balance = _bust_out(cfg, cal, b, rng, tx, payees, events, limit, balance, ramp_day, case_id)
    return tx, case


def _default(c: dict, cal: Calendar, events: list, bid: int, last_t: int, balance: float) -> None:
    missed = last_t + c["missed_payment_after_days"] * DAY
    if missed < cal.n_days * DAY:
        events.append((bid, missed, "payment_missed", None, round(balance, 2)))
        off = missed + c["charge_off_after_days"] * DAY
        if off < cal.n_days * DAY:
            events.append((bid, off, "charged_off", None, round(balance, 2)))


def _bust_out(cfg, cal, b, rng, tx, payees, events, limit, balance, ramp_day, case_id):
    t, c = cfg["typologies"]["credit_bust_out"], cfg["credit"]
    bid, op = b.business_id, b.business_id * 10
    monthly = max(b.actual_revenue, 2000.0)
    # Pump: round-trip money from a few outside accounts the owner controls, sent back out days later.
    weeks = int(rng.integers(t["ramp_weeks"][0], t["ramp_weeks"][1] + 1))
    pump_t, pump_a, back_t = [], [], []
    for w in range(weeks):
        day = ramp_day + 7 * w + int(rng.integers(0, 5))
        amt = round(monthly * rng.uniform(*t["pump_per_week_of_month"]), 2)
        pump_t.append(int(times_on(rng, np.array([day]))[0]))
        pump_a.append(amt)
        back_t.append(pump_t[-1] + int(rng.uniform(*t["pump_return_days"]) * DAY))
    n = len(pump_t)
    # The money goes back to the outside account it came from (each one also set up as a payee).
    src = rng.integers(0, 3, n)
    for k in sorted(set(src.tolist())):
        payees.add(bid * 1000 + 980 + k, bid, "external", f"External account {k + 1}", int(pump_t[0]))
    tx = _add(tx, {"business_id": bid, "account_id": op, "t": pump_t, "amount": pump_a,
                   "txn_type": np.where(rng.random(n) < 0.5, "wire_in", "ach_in").astype(object),
                   "counterparty_id": bid * 100_000 + 80_000 + src, "case_id": case_id, "role": "enabler"})
    tx = _add(tx, {"business_id": bid, "account_id": op, "t": back_t, "txn_type": "ach_out",
                   "amount": np.round(np.array(pump_a) * 0.97, 2), "payee_id": bid * 1000 + 980 + src,
                   "case_id": case_id, "role": "enabler"})

    # The increase the policy grants on the pumped inflows, then the whole line drawn and sent out.
    t_req = int((ramp_day + 7 * weeks + 1) * DAY + 11 * HOUR)
    new_limit = float(min(c["limit_cap"], max(limit * rng.uniform(*t["increase_multiple"]),
                                                round(_monthly_inflow(tx, t_req) * c["limit_share_of_monthly_inflow"], -3))))
    new_limit = round(new_limit, -3)
    events.append((bid, t_req, "limit_increase_requested", limit, None))
    events.append((bid, t_req + DAY, "limit_increased", new_limit, None))
    k = int(rng.integers(t["n_draws"][0], t["n_draws"][1] + 1))
    first = t_req + DAY + int(rng.uniform(*t["draw_after_increase_days"]) * DAY)
    draw_t = np.sort(first + (rng.uniform(0, 48, k) * HOUR).astype(np.int64))
    total = (new_limit - balance) * rng.uniform(*t["draw_share_of_available"])
    draw_a = np.round(total * rng.dirichlet(np.ones(k) * 2), 2)
    out_t = draw_t + (rng.uniform(*t["wire_out_hours"], k) * HOUR).astype(np.int64)
    out_a = np.round(draw_a * 0.97, 2)
    pid = bid * 1000 + 995
    payees.add(pid, bid, "external", "External account", int(draw_t[0] - rng.uniform(1, 24) * HOUR))
    tx = _add(tx, {"business_id": bid, "account_id": op, "t": draw_t, "txn_type": "loc_draw", "amount": draw_a,
                   "counterparty_id": 2, "case_id": case_id, "role": "enabler"})
    tx = _add(tx, {"business_id": bid, "account_id": op, "t": out_t, "amount": out_a, "payee_id": pid,
                   "txn_type": np.where(rng.random(k) < t["wire_share"], "wire_out", "ach_out").astype(object),
                   "case_id": case_id, "role": "loss", "loss_amount": out_a})
    # After the bust the account goes quiet.
    keep = (tx["t"] <= out_t.max()) | (tx["case_id"] == case_id)
    tx = {col: v[keep] for col, v in tx.items()}
    balance += float(draw_a.sum())
    _default(c, cal, events, bid, int(out_t.max()), balance)
    case = {"case_id": case_id, "business_id": bid, "typology": "credit_bust_out", "variant": b.fraud_variant,
            "account_is_fraudulent": False, "case_start_t": int(pump_t[0]), "case_end_t": int(out_t.max()),
            "loss_if_uncaught": float(out_a.sum())}
    return tx, case, balance
