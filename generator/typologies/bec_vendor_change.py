"""Business email compromise: a known vendor's bank details are changed, then the business pays the fraudster.

The victim is a good, established customer. A fraudster impersonating a real vendor gets the vendor's bank details
changed, and the business's next invoice payment(s) go to the new details. Parameters live in
config/generation.yaml under typologies.bec_vendor_change (ADR-006).

Variants
  normal_invoice  the stolen payment is the vendor's usual amount (hard to spot by amount alone).
  inflated        the fake invoice asks for a multiple of the usual amount.

The legitimate payments to that vendor between the change and its discovery are replaced by the fraud payments.
On discovery the real vendor's details are restored and the business pays the real invoice again.
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, lognormal_around, times_on
from generator.legit import Payees
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    pass


def plant(cfg: dict, cal, b: Business, rng: np.random.Generator, tx: dict, payees: Payees, ctx: dict,
          case_id: int) -> tuple[dict, dict | None]:
    t = cfg["typologies"]["bec_vendor_change"]
    vendor_ids = {v["payee_id"] for v in ctx["vendors"]}
    for attempt in range(20):
        t0 = int((b.extra["case_day"] + attempt * 3) * DAY + rng.uniform(8, 18) * HOUR)
        prior_counts = {pid: int(((tx["payee_id"] == pid) & (tx["t"] < t0)).sum()) for pid in vendor_ids}
        eligible = [pid for pid, c in sorted(prior_counts.items()) if c >= t["min_prior_payments"]
                    and ((tx["payee_id"] == pid) & (tx["t"] > t0) & (tx["t"] < t0 + 35 * DAY)).any()]
        if eligible:
            break
    else:
        return tx, None
    pid = int(eligible[rng.integers(len(eligible))])
    prior = tx["amount"][(tx["payee_id"] == pid) & (tx["t"] < t0)]
    typical = float(np.median(prior[-6:]))
    rail_prior = tx["txn_type"][(tx["payee_id"] == pid) & (tx["t"] < t0)][-1]

    payees.change_details(pid, t0)                                   # the fraudulent change
    n = int(rng.integers(t["n_payments"][0], t["n_payments"][1] + 1))
    first = t0 + int(max(1.0, lognormal_around(rng, t["payment_delay_hours_median"], t["payment_delay_hours_sigma"])) * HOUR)
    pay_t = np.sort(first + np.concatenate([[0], rng.uniform(3, 14, n - 1) * DAY]).astype(np.int64))
    mult = rng.uniform(*t[b.fraud_variant]["multiple_of_typical"], n)
    amt = np.round(typical * mult, 2)
    rail = np.where(rng.random(n) < t["wire_share"], "wire_out", rail_prior)
    t_found = int(pay_t[-1] + rng.uniform(*t["discovered_after_days"]) * DAY)
    payees.change_details(pid, t_found)                              # restored to the real vendor's account

    # Replace the legitimate payments to this vendor that fell inside the compromised window.
    drop = (tx["payee_id"] == pid) & (tx["t"] >= t0) & (tx["t"] < t_found)
    tx = {c: v[~drop] for c, v in tx.items()}
    repay_day = (t_found // DAY) + 1
    extra = {
        "t": np.concatenate([pay_t, times_on(rng, np.array([repay_day]), 9, 17)]),
        "txn_type": np.concatenate([rail, [rail_prior]]),
        "amount": np.concatenate([amt, [round(typical, 2)]]),
        "case_id": np.array([case_id] * n + [-1]),
        "role": np.array(["loss"] * n + [""], dtype=object),
        "loss_amount": np.concatenate([amt, [0.0]]),
    }
    m = n + 1
    fill = {"business_id": b.business_id, "account_id": b.business_id * 10, "counterparty_id": -1,
            "payee_id": pid, "return_after_s": -1, "return_reason": ""}
    for c in tx:
        add = extra[c] if c in extra else np.full(m, fill[c])
        tx[c] = np.concatenate([tx[c], np.asarray(add, dtype=object if tx[c].dtype == object else tx[c].dtype)])
    case = {"case_id": case_id, "business_id": b.business_id, "typology": "bec_vendor_change",
            "variant": b.fraud_variant, "account_is_fraudulent": False,
            "case_start_t": t0, "case_end_t": t_found, "loss_if_uncaught": float(amt.sum()),
            "n_checks": 0, "check_total": 0.0}
    return tx, case
