"""Online-banking events for one business: logins (with the device used), and contact-detail changes.

Owners log in from their own device, replace it now and then (a new phone), and occasionally change the email
or phone on file. A business that hires a bookkeeper sees a new device and a new email in the same week it
adds new payees - the legitimate look-alike of an account takeover.
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns, times_on
from generator.world import Business


def new_device(rng: np.random.Generator) -> str:
    return f"dev-{rng.integers(16**10):010x}"


def generate(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, ev: Columns, ctx: dict) -> None:
    e = cfg["events"]
    lo, hi = ctx["lo"], ctx["hi"]
    if hi <= lo:
        return
    owner = b.business_id * 10
    days = cal.days(lo, hi)
    rate = rng.uniform(*e["logins_per_week"]) / 7
    login_days = np.repeat(days, rng.poisson(rate, len(days)))
    t = np.sort(times_on(rng, login_days, 6, 23))

    # Device history: the owner's device, replaced at random times (a new phone or laptop).
    changes = np.sort(rng.uniform(lo, hi, rng.poisson(e["device_change_per_year"] * (hi - lo) / 365)) * DAY).astype(np.int64)
    devices = [b.extra["owner_device"]] + [new_device(rng) for _ in changes]
    which = np.searchsorted(changes, t, side="right")
    dev = np.array(devices, dtype=object)[which]
    ev.append(business_id=b.business_id, owner_id=owner, t=t, event_type="login", device_id=dev)

    n_contact = rng.poisson(e["contact_change_per_year"] * (hi - lo) / 365)
    for tc in np.sort(rng.uniform(lo, hi, n_contact) * DAY).astype(np.int64):
        kind = "email_changed" if rng.random() < 0.5 else "phone_changed"
        # A contact change happens inside a session, so the device in use is the one current at that time.
        ev.append(business_id=b.business_id, owner_id=owner, t=[int(tc)], event_type=kind,
                  device_id=[devices[int(np.searchsorted(changes, tc, side="right"))]])

    if "bookkeeper_t" in ctx:
        tb = ctx["bookkeeper_t"]
        bk_device = new_device(rng)
        ev.append(business_id=b.business_id, owner_id=owner, t=[tb, tb + int(rng.uniform(0.5, 30) * HOUR)],
                  event_type=["login", "email_changed"], device_id=[bk_device, bk_device])
        later = tb + (rng.uniform(1, 72, int(rng.integers(3, 8))) * HOUR).astype(np.int64)
        ev.append(business_id=b.business_id, owner_id=owner, t=later, event_type="login", device_id=bk_device)
