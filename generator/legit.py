"""Legitimate activity for one business: inflows by industry, biweekly payroll, vendors, card spend, transfers.

Balances are not simulated (no overdrafts); outflows are sized as shares of revenue so they roughly track inflows.
The odd-but-legitimate archetypes are applied here, because they are part of normal life at the bank.
"""
from __future__ import annotations

import numpy as np

from generator.common import DAY, HOUR, Calendar, Columns, lognormal_around, times_on
from generator.world import SUB_ACCOUNT_OPEN_DELAY_DAYS, Business, first_activity_day

VENDOR_WORDS = ["Harbor", "Summit", "Maple", "Granite", "Cedar", "Atlas", "Beacon", "Willow", "Ridge", "Prairie",
                "Copper", "Orchard", "Lantern", "Meadow", "Falcon", "Juniper", "Anchor", "Birch", "Delta", "Pioneer"]
VENDOR_KINDS = ["Supply", "Foods", "Logistics", "Rentals", "Insurance", "Software", "Wholesale", "Fuel",
                "Equipment", "Printing", "Utilities", "Staffing", "Packaging", "Hardware"]


class Payees:
    """Payee master data and the event history (created, bank details changed) for every business."""

    def __init__(self):
        self.rows: list[dict] = []
        self.events: list[tuple[int, int, str, int]] = []   # (payee_id, t, event_type, details_version)
        self.version: dict[int, int] = {}

    def add(self, payee_id: int, business_id: int, payee_type: str, name: str, created_t: int) -> None:
        self.rows.append({"payee_id": payee_id, "business_id": business_id, "payee_type": payee_type,
                          "payee_name": name, "created_t": created_t})
        self.events.append((payee_id, created_t, "created", 0))
        self.version[payee_id] = 0

    def change_details(self, payee_id: int, t: int) -> int:
        version = self.version[payee_id] + 1
        self.version[payee_id] = version
        self.events.append((payee_id, t, "bank_details_changed", version))
        return version


def season_curve(cfg: dict, b: Business) -> np.ndarray:
    s = np.array(cfg["industries"][b.industry]["season"], dtype=float)
    if b.archetype == "seasonal_heavy":
        a = cfg["odd_archetypes"]["seasonal_heavy"]
        # Sharpen the industry curve: winter falls to the floor, the peak rises well above the mean.
        s = np.maximum(a["winter_floor"], s ** a["sharpen_power"])
        s = s / s.mean()
    return s


def daily_revenue(cfg: dict, cal: Calendar, b: Business, days: np.ndarray) -> np.ndarray:
    s = season_curve(cfg, b)
    growth = (1 + b.growth_per_year) ** (cal.at(cal.month_ordinal, days) / 12)
    return b.actual_revenue * s[cal.at(cal.month, days)] * growth / 30.4


def generate(cfg: dict, cal: Calendar, b: Business, rng: np.random.Generator, txns: Columns, payees: Payees) -> dict:
    """Write one business's legitimate activity. Returns per-business context the typologies reuse."""
    lo = first_activity_day(cal, b)
    hi = b.end_day if b.end_day is not None else cal.n_days
    icfg, L = cfg["industries"][b.industry], cfg["legit"]
    bid, op = b.business_id, b.business_id * 10
    ctx = {"lo": lo, "hi": hi, "vendors": [], "clients": []}
    if hi <= lo:
        return ctx
    days = cal.days(lo, hi)
    bdays = cal.business_days(lo, hi)
    rev_b = daily_revenue(cfg, cal, b, bdays) * 7 / 5   # revenue spread over business days only
    mix = dict(icfg["inflow_mix"])
    if b.archetype == "many_small_checks":
        mix = {"card": mix["card"] * 0.4, "ach_client": mix["ach_client"] * 0.4}
        mix["check"] = 1 - sum(mix.values())

    # Clients: the counterparties that pay this business, with a few big ones (Zipf-like weights).
    n_lo, n_hi = icfg["n_clients"]
    n_clients = int(rng.integers(n_lo, n_hi + 1))
    clients = bid * 100_000 + np.arange(n_clients)
    cw = 1 / np.arange(1, n_clients + 1) ** 0.8
    cw /= cw.sum()
    ctx["clients"] = clients

    # Card settlements: the processor batches deposits three times a week (Mon, Wed, Fri).
    if mix.get("card", 0) > 0:
        sdays = bdays[np.isin(cal.at(cal.dow, bdays), [0, 2, 4])]
        amt = daily_revenue(cfg, cal, b, sdays) * 7 / 3 * mix["card"] * lognormal_around(rng, 1.0, 0.25, len(sdays))
        txns.append(business_id=bid, account_id=op, t=sdays * DAY + 6 * HOUR + rng.integers(0, HOUR, len(sdays)),
                    txn_type="card_settlement", amount=np.round(amt, 2), counterparty_id=1)

    # Client ACH and check payments: invoice-sized, at a Poisson rate.
    limit = L["mobile_deposit_limit_per_check"]
    for kind, share in (("ach_in", mix.get("ach_client", 0)), ("mobile_check_deposit", mix.get("check", 0))):
        if share <= 0:
            continue
        if kind == "mobile_check_deposit" and b.archetype == "many_small_checks":
            a = cfg["odd_archetypes"]["many_small_checks"]
            avg = float(np.mean(a["check_amount"]))
            payer_pool = bid * 100_000 + 1_000 + np.arange(int(rng.integers(*a["n_payers"])))
        else:
            avg = b.actual_revenue * share / max(1.0, min(25.0, n_clients * 0.4))
            payer_pool = None
        counts = rng.poisson(rev_b * share / avg)
        d = np.repeat(bdays, counts)
        if len(d) == 0:
            continue
        if payer_pool is not None:
            lo_a, hi_a = cfg["odd_archetypes"]["many_small_checks"]["check_amount"]
            amount = rng.uniform(lo_a, hi_a, len(d))
            payer = rng.choice(payer_pool, len(d))
        else:
            amount = lognormal_around(rng, avg, 0.5, len(d))
            payer = rng.choice(clients, len(d), p=cw)
            if kind == "mobile_check_deposit":
                # Some checks come from one-off payers the business has not seen before.
                new = rng.random(len(d)) < L["new_check_payer_share"]
                payer = np.where(new, bid * 100_000 + 50_000 + np.arange(len(d)), payer)
        ret = np.full(len(d), -1, dtype=np.int64)
        reason = np.full(len(d), "", dtype=object)
        if kind == "mobile_check_deposit":
            returned = rng.random(len(d)) < L["check_return_rate"]
            ret[returned] = (rng.uniform(2, 6, returned.sum()) * DAY).astype(np.int64)
            reason[returned] = "nsf"
        txns.append(business_id=bid, account_id=op, t=times_on(rng, d), txn_type=kind,
                    amount=np.round(np.clip(amount, 5, limit if kind == "mobile_check_deposit" else None), 2), counterparty_id=payer,
                    return_after_s=ret, return_reason=reason)

    # Payroll: biweekly Fridays from the payroll sub-account, funded the day before by an internal transfer.
    if b.has_payroll:
        payroll_payee = bid * 1000 + 999
        payees.add(payroll_payee, bid, "payroll_provider", "Payroll run", lo * DAY - DAY)
        share = icfg["payroll_share"]
        fridays = days[cal.at(cal.dow, days) == 4]
        fridays = fridays[int(rng.integers(0, 2))::2]
        # The funding transfer lands once the payroll sub-account is open.
        fridays = fridays[fridays - 1 >= max(lo, b.open_day + SUB_ACCOUNT_OPEN_DELAY_DAYS)]
        if len(fridays):
            # Payroll follows revenue loosely (staff hours flex with the season), not one to one.
            rev = daily_revenue(cfg, cal, b, fridays) * 30.4
            amt = np.round((b.actual_revenue * 0.5 + rev * 0.5) * share * 12 / 26 * lognormal_around(rng, 1, 0.04, len(fridays)), 2)
            t_pay = fridays * DAY + 9 * HOUR
            t_fund = t_pay - DAY + rng.integers(0, 4 * HOUR, len(fridays))
            txns.append(business_id=bid, account_id=op, t=t_fund, txn_type="internal_transfer_out", amount=amt)
            txns.append(business_id=bid, account_id=op + 2, t=t_fund, txn_type="internal_transfer_in", amount=amt)
            txns.append(business_id=bid, account_id=op + 2, t=t_pay, txn_type="payroll", amount=amt, payee_id=payroll_payee)

    # Vendors: each with a cadence and a typical amount; occasional legitimate bank-detail changes.
    n_v = int(rng.integers(*L["vendor_count"]))
    vw = rng.dirichlet(np.ones(n_v) * 0.8)
    change_rate = L["vendor_details_change_per_year"]
    if b.archetype == "vendor_details_churn":
        change_rate = cfg["odd_archetypes"]["vendor_details_churn"]["changes_per_vendor_year"]
    span_years = (hi - lo) / 365
    for k in range(n_v):
        pid = bid * 1000 + k
        name = f"{VENDOR_WORDS[rng.integers(len(VENDOR_WORDS))]} {VENDOR_KINDS[rng.integers(len(VENDOR_KINDS))]}"
        payees.add(pid, bid, "vendor", name, lo * DAY - int(rng.uniform(1, 30)) * DAY)
        cadence = rng.choice([30, 14, 7], p=[0.7, 0.22, 0.08])
        monthly = b.actual_revenue * L["vendor_outflow_share"] * vw[k]
        typical = monthly * cadence / 30.4
        if typical < 50:
            continue
        pay_days = np.arange(lo + int(rng.integers(0, cadence)), hi, cadence)
        pay_days = cal.next_business_day(pay_days + rng.integers(-2, 3, len(pay_days)))
        pay_days = pay_days[(pay_days >= lo) & (pay_days < hi)]
        if len(pay_days) == 0:
            continue
        s = season_curve(cfg, b)[cal.at(cal.month, pay_days)] ** 0.7
        amt = np.round(typical * s * lognormal_around(rng, 1, 0.15, len(pay_days)), 2)
        rail = "wire_out" if typical > L["wire_if_typical_over"] and rng.random() < L["wire_share_for_large"] else "ach_out"
        txns.append(business_id=bid, account_id=op, t=times_on(rng, pay_days, 9, 17), txn_type=rail,
                    amount=amt, payee_id=pid)
        for t_change in np.sort(rng.uniform(lo, hi, rng.poisson(change_rate * span_years)) * DAY).astype(np.int64):
            payees.change_details(pid, int(t_change))
        ctx["vendors"].append({"payee_id": pid, "typical": typical, "rail": rail})

    # Owner draws to the owner's own external account, roughly monthly.
    owner_pid = bid * 1000 + 998
    payees.add(owner_pid, bid, "owner_external", "Owner external account", lo * DAY - 5 * DAY)
    draw_days = cal.next_business_day(np.arange(lo + int(rng.integers(0, 30)), hi, 30))
    draw_days = draw_days[draw_days < hi]
    txns.append(business_id=bid, account_id=op, t=times_on(rng, draw_days), txn_type="ach_out",
                amount=np.round(lognormal_around(rng, b.actual_revenue * L["owner_draw_share"], 0.3, len(draw_days)), 2),
                payee_id=owner_pid)

    # Owner top-ups: some owners fund the business by pulling from their own account (ACH debit), monthly.
    if rng.random() < L["owner_topup_share"]:
        tdays = cal.next_business_day(np.arange(lo + int(rng.integers(0, 30)), hi, 30))
        tdays = tdays[tdays < hi]
        amt = np.round(b.actual_revenue * rng.uniform(*L["owner_topup_of_revenue"]) * lognormal_around(rng, 1, 0.3, len(tdays)), 2)
        ret = np.full(len(tdays), -1, dtype=np.int64)
        returned = rng.random(len(tdays)) < L["owner_topup_return_rate"]
        ret[returned] = (rng.uniform(2, 4, returned.sum()) * DAY).astype(np.int64)
        txns.append(business_id=bid, account_id=op, t=times_on(rng, tdays), txn_type="ach_debit_in", amount=amt,
                    counterparty_id=bid * 100_000 + 99_999, return_after_s=ret,
                    return_reason=np.where(returned, "nsf", "").astype(object))

    # Tax reserve: a monthly sweep into the tax sub-account.
    if b.has_tax_account:
        tdays = cal.next_business_day(np.arange(lo + 15, hi, 30))
        tdays = tdays[tdays < hi]
        amt = np.round(daily_revenue(cfg, cal, b, tdays) * 30.4 * L["tax_transfer_share"], 2)
        tt = times_on(rng, tdays)
        txns.append(business_id=bid, account_id=op, t=tt, txn_type="internal_transfer_out", amount=amt)
        txns.append(business_id=bid, account_id=op + 1, t=tt, txn_type="internal_transfer_in", amount=amt)

    # Card spend: many small purchases.
    lo_c, hi_c = L["card_spend_per_month"]
    per_month = np.clip(lo_c + np.log10(max(b.actual_revenue, 1000) / 1000) * 8, lo_c, hi_c)
    counts = rng.poisson(per_month / 30.4, len(days))
    d = np.repeat(days, counts)
    if len(d):
        avg = b.actual_revenue * L["card_spend_share"] / per_month
        txns.append(business_id=bid, account_id=op, t=times_on(rng, d, 7, 22), txn_type="card_spend",
                    amount=np.round(np.maximum(lognormal_around(rng, avg, 0.8, len(d)), 3), 2))

    _apply_archetype_events(cfg, cal, b, rng, txns, ctx, clients)
    _apply_phase2_archetypes(cfg, cal, b, rng, txns, payees, ctx)
    return ctx


def _apply_archetype_events(cfg, cal, b, rng, txns, ctx, clients) -> None:
    """One-off legitimate events that look like fraud: lumpy contractor checks and annual big invoices."""
    bid, op = b.business_id, b.business_id * 10
    lo, hi = ctx["lo"], ctx["hi"]
    span_years = (hi - lo) / 365
    vendors = ctx["vendors"]
    if b.archetype == "lumpy_contractor" and vendors:
        a = cfg["odd_archetypes"]["lumpy_contractor"]
        n = rng.poisson(rng.uniform(*a["lumps_per_year"]) * span_years)
        for day in rng.integers(lo, hi - 3, n) if hi - 3 > lo else []:
            amount = round(min(b.actual_revenue * rng.uniform(*a["lump_multiple_of_month"]),
                               cfg["legit"]["mobile_deposit_limit_per_check"]), 2)
            t0 = int(times_on(rng, np.array([day]))[0])
            txns.append(business_id=bid, account_id=op, t=[t0], txn_type="mobile_check_deposit", amount=[amount],
                        counterparty_id=[int(rng.choice(clients[:3]))])
            spend = amount * rng.uniform(*a["spend_share_within_3d"])
            parts = rng.dirichlet(np.ones(int(rng.integers(1, 4))))
            for p in parts:
                v = vendors[int(rng.integers(len(vendors)))]
                txns.append(business_id=bid, account_id=op, t=[t0 + int(rng.uniform(2, 72) * HOUR)],
                            txn_type=v["rail"], amount=[round(spend * p, 2)], payee_id=[v["payee_id"]])
    if b.archetype == "annual_big_invoice" and vendors:
        a = cfg["odd_archetypes"]["annual_big_invoice"]
        v = vendors[int(rng.integers(len(vendors)))]
        first = lo + int(rng.integers(30, 365))
        for day in cal.next_business_day(np.arange(first, hi, 365)):
            if day < hi:
                txns.append(business_id=bid, account_id=op, t=times_on(rng, np.array([day]), 9, 17),
                            txn_type=v["rail"], amount=[round(v["typical"] * rng.uniform(*a["multiple_of_typical"]), 2)],
                            payee_id=[v["payee_id"]])


def _apply_phase2_archetypes(cfg, cal, b, rng, txns, payees, ctx) -> None:
    """Look-alikes for mules (many small transfers, swept out) and account takeover (a new bookkeeper)."""
    bid, op = b.business_id, b.business_id * 10
    lo, hi = ctx["lo"], ctx["hi"]
    if b.archetype == "many_small_transfers":
        a = cfg["odd_archetypes"]["many_small_transfers"]
        senders = bid * 100_000 + 20_000 + np.arange(int(rng.integers(*a["n_senders"])))
        days = cal.days(lo, hi)
        per_day = rng.uniform(*a["payments_per_month"]) / 30.4
        d = np.repeat(days, rng.poisson(per_day, len(days)))
        if len(d):
            t = times_on(rng, d, 0, 24)
            amt = np.round(rng.uniform(*a["amount"], len(d)), 2)
            txns.append(business_id=bid, account_id=op, t=t, txn_type="ach_in", amount=amt, counterparty_id=rng.choice(senders, len(d)))
            # A weekly sweep of most of the week's takings to the owner's own account.
            share = rng.uniform(*a["sweep_share"])
            for week_start in range(lo, hi - 7, 7):
                in_week = amt[(t >= week_start * DAY) & (t < (week_start + 7) * DAY)].sum()
                if in_week > 0:
                    txns.append(business_id=bid, account_id=op, t=times_on(rng, cal.next_business_day(np.array([week_start + 7]))),
                                txn_type="ach_out", amount=[round(in_week * share, 2)], payee_id=[bid * 1000 + 998])
    if b.archetype == "new_bookkeeper" and hi - lo > 60:
        a = cfg["odd_archetypes"]["new_bookkeeper"]
        tb = int((rng.uniform(lo + 30, hi - 20)) * DAY)
        ctx["bookkeeper_t"] = tb
        for k in range(int(rng.integers(a["new_payees"][0], a["new_payees"][1] + 1))):
            pid = bid * 1000 + 900 + k
            created = tb + int(rng.uniform(2, 72) * HOUR)
            payees.add(pid, bid, "vendor", f"{VENDOR_WORDS[rng.integers(len(VENDOR_WORDS))]} {VENDOR_KINDS[rng.integers(len(VENDOR_KINDS))]}", created)
            typical = b.actual_revenue * rng.uniform(0.02, 0.08)
            pay_days = np.arange(created // DAY + 1, hi, 30)
            if len(pay_days):
                txns.append(business_id=bid, account_id=op, t=times_on(rng, cal.next_business_day(pay_days), 9, 17),
                            txn_type="ach_out", amount=np.round(typical * lognormal_around(rng, 1, 0.15, len(pay_days)), 2),
                            payee_id=pid)
