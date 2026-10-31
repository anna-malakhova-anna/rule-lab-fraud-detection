"""First-party ACH return fraud: the EMERGING pattern, starting in month 12 (ADR-014).

The business pulls money in by ACH debit from external accounts it does not control (it claims they are its
own), withdraws most of it as soon as the funds are available, and the debits come back days later as
unauthorized. No Phase 1 rule looks at ACH debits, so this is meant to surface first in monitoring (a rise in
unauthorized ACH returns that no alert preceded), then be investigated and answered with a new rule.
Parameters: config/generation.yaml typologies.ach_return_fraud.

Legitimate ACH debits exist all along: owners topping up the business from their own account (generator/legit.py).
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns, times_on
from generator.legit import Payees, season_curve
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    b.end_day = b.extra["case_day"] + 12


def plant(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees,
          case_id: int) -> dict:
    t = cfg["typologies"]["ach_return_fraud"]
    bid, op = b.business_id, b.business_id * 10
    day = b.extra["case_day"]
    monthly = b.actual_revenue * season_curve(cfg, b)[cal.at(cal.month, np.array([day]))[0]]
    n = int(rng.integers(t["n_pulls"][0], t["n_pulls"][1] + 1))
    pull_t = np.sort(times_on(rng, day + rng.integers(0, t["pull_days"][1], n)))
    amt = np.round(np.minimum(t["pull_cap"] * rng.uniform(0.6, 1.0, n), monthly * rng.uniform(*t["pull_multiple_of_month"], n)), 2)
    amt = np.maximum(amt, 1000.0)
    ret = (rng.uniform(*t["return_days"], n) * DAY).astype(np.int64)
    txns.append(business_id=bid, account_id=op, t=pull_t, txn_type="ach_debit_in", amount=amt,
                counterparty_id=bid * 100_000 + 95_000 + np.arange(n), return_after_s=ret,
                return_reason=np.full(n, "unauthorized", dtype=object), case_id=case_id, role="enabler")

    first = int(pull_t[0] + rng.uniform(*t["first_withdrawal_hours"]) * HOUR)
    k = int(rng.integers(t["n_withdrawals"][0], t["n_withdrawals"][1] + 1))
    w_t = np.sort(first + np.concatenate([[0], rng.uniform(1, 30, k - 1) * HOUR]).astype(np.int64))
    w_amt = np.round(amt.sum() * rng.uniform(*t["withdrawn_share"]) * rng.dirichlet(np.ones(k) * 2), 2)
    pid = bid * 1000 + 994
    payees.add(pid, bid, "external", "External account", first - int(rng.uniform(1, 48) * HOUR))
    dest = np.where(rng.random(k) < 0.7, pid, bid * 1000 + 998)
    txns.append(business_id=bid, account_id=op, t=w_t, txn_type=np.where(rng.random(k) < t["wire_share"], "wire_out", "ach_out"),
                amount=w_amt, payee_id=dest, case_id=case_id, role="loss", loss_amount=w_amt)
    return {"case_id": case_id, "business_id": bid, "typology": "ach_return_fraud", "variant": b.fraud_variant,
            "account_is_fraudulent": bool(b.extra["new_account"]),
            "case_start_t": int(pull_t[0]), "case_end_t": int((pull_t + ret).max()),
            "loss_if_uncaught": float(w_amt.sum())}
