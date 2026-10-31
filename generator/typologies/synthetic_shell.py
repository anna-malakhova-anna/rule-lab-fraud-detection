"""Synthetic or shell businesses: rings of applicants that share devices, phones, an address and an email domain.

Identity sharing and ring formation happen in generator/world.py (the ring's applications, including some the
bank's existing checks already declined). Here: the account is funded fast from outside, runs a little
invented activity, then busts out with bad checks (the check_deposit_fraud mechanics, scaled to the revenue
the shell claimed). Parameters: config/generation.yaml typologies.synthetic_shell (ADR-012).

Signals: shared identity attributes with other applicants, very recent incorporation, fast first funding,
stated revenue far above real activity, then the bust-out signals of deposit fraud.
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, Calendar, Columns, pick, times_on
from generator.legit import Payees
from generator.typologies import check_deposit_fraud
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    b.end_day = b.extra["case_day"] + 10


def plant(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees,
          case_id: int) -> dict:
    t = cfg["typologies"]["synthetic_shell"]
    bid = b.business_id
    # Fast first funding from an outside account, within days of opening.
    day = b.open_day + int(rng.integers(t["first_funding_days"][0], t["first_funding_days"][1] + 1))
    txns.append(business_id=bid, account_id=bid * 10, t=times_on(rng, np.array([day])), txn_type="wire_in",
                amount=[round(float(rng.uniform(*t["first_funding_amount"])), 2)], counterparty_id=[bid * 100_000 + 97_000],
                case_id=case_id, role="enabler")
    variant = pick(rng, cfg["typologies"]["check_deposit_fraud"]["variants"])
    case = check_deposit_fraud.plant(cfg, cal, b, rng, txns, payees, case_id, typology="synthetic_shell",
                                     variant=variant, monthly=b.stated_revenue * t["bust_share_of_stated_revenue"])
    case["variant"] = f"ring_{variant}"
    case["ring_id"] = b.extra["ring_id"]
    case["case_start_t"] = b.open_day * DAY     # the whole account is the scheme
    return case
