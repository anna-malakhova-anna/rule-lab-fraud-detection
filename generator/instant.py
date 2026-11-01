"""Instant payouts, launched part-way through the test months (module C, ADR-021).

From the launch date, outbound ACH and wire payments to a payee (never payroll) can go out as `instant_payout`.
Some honest businesses adopt it for part of their payments, up to the per-payout cap. Fraudsters adapt: most
cash-outs after launch switch to instant, and a cash-out above the cap is split into several payouts under it,
minutes apart. Applied to the finished transaction arrays, before transaction ids are assigned.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

from generator.common import DAY, Calendar

ELIGIBLE = ("ach_out", "wire_out")


def launch_t(cfg: dict, cal: Calendar) -> int:
    launch = dt.date.fromisoformat(cfg["instant_payouts"]["launch_date"])
    return (launch - cal.start).days * DAY


def apply(cfg: dict, cal: Calendar, rng: np.random.Generator, tx: dict, n_businesses: int) -> dict:
    c = cfg["instant_payouts"]
    eligible = np.isin(tx["txn_type"], ELIGIBLE) & (tx["payee_id"] >= 0) & (tx["t"] >= launch_t(cfg, cal))
    is_fraud = tx["role"] == "loss"

    # Honest adoption: a per-business decision and share, under the cap.
    adopts = rng.random(n_businesses + 1) < c["legit_adoption"]
    share = rng.uniform(*c["legit_share_of_payments"], n_businesses + 1)
    biz = tx["business_id"].astype(np.int64)
    legit_switch = eligible & ~is_fraud & adopts[biz] & (rng.random(len(biz)) < share[biz]) & (tx["amount"] <= c["per_payout_cap"])
    tx["txn_type"] = np.where(legit_switch, "instant_payout", tx["txn_type"]).astype(object)

    # Fraud adapts: most cash-outs switch, and big ones are split under the cap.
    fraud_switch = eligible & is_fraud & (rng.random(len(biz)) < c["fraud_adoption"])
    keep = ~fraud_switch
    pieces = {col: [v[keep]] for col, v in tx.items()}
    for i in np.flatnonzero(fraud_switch):
        k = int(np.ceil(tx["amount"][i] / c["per_payout_cap"]))
        amounts = np.round(np.full(k, tx["amount"][i] / k), 2)
        amounts[-1] = round(tx["amount"][i] - amounts[:-1].sum(), 2)
        gaps = np.concatenate([[0], np.cumsum(rng.uniform(*c["split_gap_minutes"], k - 1) * 60)]).astype(np.int64)
        for col, v in tx.items():
            if col == "t":
                part = v[i] + gaps
            elif col == "amount":
                part = amounts
            elif col == "loss_amount":
                part = amounts
            elif col == "txn_type":
                part = np.full(k, "instant_payout", dtype=object)
            else:
                part = np.full(k, v[i], dtype=v.dtype)
            pieces[col].append(part)
    return {col: np.concatenate(parts) for col, parts in pieces.items()}
