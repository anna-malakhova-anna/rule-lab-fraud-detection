"""Account takeover: a fraudster gets into a good customer's online banking and pays themselves.

The sequence, within hours: a login from a device never seen on the account, a change to the email (and often
the phone) on file so alerts go to the fraudster, a new external payee, then one or more payouts. The owner
notices days later. Parameters: config/generation.yaml typologies.account_takeover (ADR-012).

The legitimate look-alikes: owners who get a new phone, and businesses that hire a bookkeeper (new device,
new email, new payees in one week; the new_bookkeeper archetype).
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns
from generator.events import new_device
from generator.legit import Payees, season_curve
from generator.world import Business


def plan(cfg: dict, b: Business) -> None:
    pass


def plant(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees,
          ev: Columns, case_id: int) -> dict:
    t = cfg["typologies"]["account_takeover"]
    bid, op, owner = b.business_id, b.business_id * 10, b.business_id * 10
    t0 = int(b.extra["case_day"] * DAY + rng.uniform(0, 24) * HOUR)
    dev = new_device(rng)
    t_contact = t0 + int(rng.uniform(*t["contact_change_hours"]) * HOUR)
    kinds = ["email_changed"] + (["phone_changed"] if b.fraud_variant == "email_and_phone" else [])
    ev.append(business_id=bid, owner_id=owner, t=[t0] + [t_contact + i * 600 for i in range(len(kinds))],
              event_type=["login"] + kinds, device_id=[dev] * (1 + len(kinds)), is_fraud=True)

    pid = bid * 1000 + 993
    t_payee = t0 + int(rng.uniform(*t["new_payee_hours"]) * HOUR)
    payees.add(pid, bid, "external", "External account", t_payee)
    k = int(rng.integers(t["n_payouts"][0], t["n_payouts"][1] + 1))
    monthly = b.actual_revenue * season_curve(cfg, b)[cal.at(cal.month, np.array([b.extra["case_day"]]))[0]]
    total = float(np.clip(monthly * rng.uniform(*t["payout_multiple_of_month"]), t["payout_min"], t["payout_cap"]))
    pay_t = np.sort(np.maximum(t_payee + 300, t0 + (rng.uniform(*t["payout_hours"], k) * HOUR).astype(np.int64)))
    amt = np.round(total * rng.dirichlet(np.ones(k) * 2), 2)
    txns.append(business_id=bid, account_id=op, t=pay_t, txn_type=np.where(rng.random(k) < 0.6, "wire_out", "ach_out"),
                amount=amt, payee_id=pid, case_id=case_id, role="loss", loss_amount=amt)
    ev.append(business_id=bid, owner_id=owner, t=pay_t - 120, event_type="login", device_id=dev, is_fraud=True)
    t_report = int(pay_t[-1] + rng.uniform(*t["owner_notices_days"]) * DAY)
    return {"case_id": case_id, "business_id": bid, "typology": "account_takeover", "variant": b.fraud_variant,
            "account_is_fraudulent": False, "case_start_t": t0, "case_end_t": t_report,
            "loss_if_uncaught": float(amt.sum())}
