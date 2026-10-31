"""Money mules: an account that collects many small payments from unrelated senders and sweeps them out fast.

The money belongs to scam victims elsewhere. The bank's exposure is the swept amount (recall requests,
reimbursement and regulatory cost), counted here as the loss if uncaught. Parameters:
config/generation.yaml typologies.money_mule (ADR-012).

Variants
  recruited_new      an account opened for the purpose, with little genuine activity.
  existing_business  an established small business that lets its account be used.

Signals: many first-time senders in a short span, money out within a day or two, activity unrelated to the
stated industry. The legitimate look-alike is the many_small_transfers archetype (generator/legit.py).
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns, times_on
from generator.legit import Payees
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    t = cfg["typologies"]["money_mule"]
    b.end_day = b.extra["case_day"] + t["active_days"][1] + 5


def plant(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees,
          case_id: int) -> dict:
    t = cfg["typologies"]["money_mule"]
    bid, op = b.business_id, b.business_id * 10
    start = b.extra["case_day"]
    span = int(rng.integers(*t["active_days"]))
    n = int(rng.integers(*t["n_inbound"]))
    in_t = np.sort(times_on(rng, start + rng.integers(0, span, n), 0, 24))
    in_amt = np.round(rng.uniform(*t["inbound_amount"], n), 2)
    rail_in = np.where(rng.random(n) < t["wire_share_inbound"], "wire_in", "ach_in")
    senders = bid * 100_000 + 60_000 + np.arange(n)            # every sender is new and pays once
    txns.append(business_id=bid, account_id=op, t=in_t, txn_type=rail_in, amount=in_amt, counterparty_id=senders,
                case_id=case_id, role="enabler")

    dest = [bid * 1000 + 991, bid * 1000 + 992]
    for k, pid in enumerate(dest):
        payees.add(pid, bid, "external", f"External account {k + 1}", int(in_t[0] + rng.uniform(1, 24) * HOUR))
    # Sweep everything received since the last sweep, every 1-3 days.
    sweeps_t, sweeps_amt = [], []
    t_cursor, last = int(in_t[0]), 0
    end = int(in_t[-1]) + DAY
    while t_cursor < end:
        t_cursor += int(rng.uniform(*t["sweep_every_days"]) * DAY)
        got = in_amt[(in_t > last) & (in_t <= t_cursor)].sum()
        if got > 0:
            sweeps_t.append(t_cursor + int(rng.uniform(0, 6) * HOUR))
            sweeps_amt.append(round(got * rng.uniform(*t["sweep_share"]), 2))
        last = t_cursor
    m = len(sweeps_t)
    out_amt = np.array(sweeps_amt)
    txns.append(business_id=bid, account_id=op, t=np.array(sweeps_t, dtype=np.int64),
                txn_type=np.where(rng.random(m) < t["wire_share_out"], "wire_out", "ach_out"), amount=out_amt,
                payee_id=np.array(dest)[rng.integers(0, 2, m)], case_id=case_id, role="loss", loss_amount=out_amt)
    return {"case_id": case_id, "business_id": bid, "typology": "money_mule", "variant": b.fraud_variant,
            "account_is_fraudulent": bool(b.extra["new_account"]),
            "case_start_t": int(in_t[0]), "case_end_t": int(max(sweeps_t)),
            "loss_if_uncaught": float(out_amt.sum())}
