"""Mobile check deposit fraud (bad checks, kiting).

The scheme: deposit one or more checks that will bounce, withdraw most of the money before they are returned,
then go quiet. Parameters live in config/generation.yaml under typologies.check_deposit_fraud (ADR-006).

Variants
  single_large  1-2 large checks, each a multiple of the account's normal monthly inflow.
  multi_payer   4-12 smaller checks from different payers the business has never been paid by, over a few days.

Each check stays under the per-check mobile deposit limit (legit.mobile_deposit_limit_per_check).

Signals left behind for the rules: a deposit far above the account's own baseline, outbound money soon after it,
many distinct check payers in a short span, and returns 2-7 days later. Loss = every withdrawal funded by the
bad checks (withdrawals are sized below the check total, so all of it is loss).
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns, lognormal_around, pick, times_on
from generator.legit import Payees, season_curve
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    """Called before legitimate activity: the account goes quiet shortly after the scheme."""
    b.end_day = b.extra["case_day"] + 10


def plant(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees,
          case_id: int, typology: str = "check_deposit_fraud", variant: str | None = None,
          monthly: float | None = None) -> dict:
    """Plant the scheme. Shell businesses reuse it for their bust-out (typology, variant and the monthly
    scale are then passed in)."""
    t = cfg["typologies"]["check_deposit_fraud"]
    bid, op = b.business_id, b.business_id * 10
    day = b.extra["case_day"]
    variant = variant or b.fraud_variant
    if monthly is None:
        monthly = b.actual_revenue * season_curve(cfg, b)[cal.at(cal.month, np.array([day]))[0]]

    if variant == "single_large":
        v = t["single_large"]
        n = int(rng.integers(v["n_checks"][0], v["n_checks"][1] + 1))
        amounts = np.maximum(v["min_amount"], monthly * rng.uniform(*v["multiple_of_month"], n))
        dep_t = times_on(rng, np.full(n, day))
    else:
        v = t["multi_payer"]
        n = int(rng.integers(v["n_checks"][0], v["n_checks"][1] + 1))
        span = int(rng.integers(v["days"][0], v["days"][1] + 1))
        amounts = np.maximum(v["min_amount"], monthly * rng.uniform(*v["multiple_of_month"], n))
        dep_t = np.sort(times_on(rng, day + rng.integers(0, span, n), 7, 23))
    # Fraudsters probe the per-check mobile deposit limit rather than exceed it.
    limit = cfg["legit"]["mobile_deposit_limit_per_check"]
    amounts = np.round(np.where(amounts > limit, limit * rng.uniform(0.6, 1.0, n), amounts), 2)
    payers = bid * 100_000 + 90_000 + np.arange(n)          # payers this business has never seen
    ret_after = (rng.uniform(*t["return_days"], n) * DAY).astype(np.int64)
    reasons = np.array([pick(rng, t["return_reasons"]) for _ in range(n)], dtype=object)
    txns.append(business_id=bid, account_id=op, t=dep_t, txn_type="mobile_check_deposit", amount=amounts,
                counterparty_id=payers, return_after_s=ret_after, return_reason=reasons,
                case_id=case_id, role="enabler")

    # Withdrawals: start hours after the first deposit, go to a freshly added external payee or the owner's account.
    first = int(dep_t[0] + lognormal_around(rng, t["first_withdrawal_hours_median"], t["first_withdrawal_hours_sigma"]) * HOUR)
    first = max(first, int(dep_t[0]) + 20 * 60)
    k = int(rng.integers(t["n_withdrawals"][0], t["n_withdrawals"][1] + 1))
    w_t = np.sort(first + np.concatenate([[0], rng.uniform(1, 36, k - 1) * HOUR]).astype(np.int64))
    total = amounts.sum() * rng.uniform(*t["withdrawn_share"])
    w_amt = np.round(total * rng.dirichlet(np.ones(k) * 2), 2)
    new_payee = bid * 1000 + 990
    payees.add(new_payee, bid, "external", "External account", first - int(rng.uniform(0.5, 48) * HOUR))
    dest = np.where(rng.random(k) < 0.7, new_payee, bid * 1000 + 998)
    rail = np.where(rng.random(k) < t["wire_share"], "wire_out", "ach_out")
    txns.append(business_id=bid, account_id=op, t=w_t, txn_type=rail, amount=w_amt, payee_id=dest,
                case_id=case_id, role="loss", loss_amount=w_amt)

    return {"case_id": case_id, "business_id": bid, "typology": typology, "variant": variant,
            "account_is_fraudulent": bool(b.extra["new_account"]),
            "case_start_t": int(dep_t[0]), "case_end_t": int((dep_t + ret_after).max()),
            "loss_if_uncaught": float(w_amt.sum()), "n_checks": n, "check_total": float(amounts.sum())}
