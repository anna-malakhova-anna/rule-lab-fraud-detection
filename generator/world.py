"""Businesses, owners and accounts, plus which businesses get an odd-but-legitimate archetype or a fraud case.

Assignments are drawn here, before any activity, so each activity generator knows how a business behaves.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
from faker import Faker

from generator.common import DAY, Calendar, lognormal_around, pick, rng_for

STATES = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI", "NJ", "VA", "WA", "AZ", "MA",
          "TN", "IN", "MO", "MD", "WI", "CO", "MN", "SC", "AL", "LA", "OR", "UT", "NV"]
SUB_ACCOUNTS = {0: "operating", 1: "tax_reserve", 2: "payroll"}


@dataclass
class Business:
    business_id: int
    industry: str
    stated_revenue: float        # what the applicant said, per month
    actual_revenue: float        # what the business really does, per month (before seasonality)
    growth_per_year: float
    open_day: int                # day index the account opened (can be before the warm-up)
    incorporation_day: int
    state: str
    has_payroll: bool
    has_tax_account: bool
    archetype: str = "standard"
    fraud: str | None = None     # typology name, if a fraud case is planted
    fraud_variant: str | None = None
    end_day: int | None = None   # activity stops here (fraud accounts go quiet after the scheme)
    extra: dict = field(default_factory=dict)

    @property
    def size_band(self) -> str:
        r = self.stated_revenue
        return "micro" if r < 20_000 else "small" if r < 100_000 else "mid"

    def account_ids(self) -> list[int]:
        subs = [0] + ([1] if self.has_tax_account else []) + ([2] if self.has_payroll else [])
        return [self.business_id * 10 + s for s in subs]


def build_businesses(cfg: dict, cal: Calendar) -> list[Business]:
    rng = rng_for(cfg["seed"], "world")
    pop = cfg["population"]
    inds = cfg["industries"]
    names = list(inds)
    w = np.array([inds[n]["weight"] for n in names])
    out = []
    for i in range(pop["n_businesses"]):
        ind = names[rng.choice(len(names), p=w / w.sum())]
        icfg = inds[ind]
        stated = float(np.clip(lognormal_around(rng, icfg["rev_median"], 0.8), 3_000, 1_500_000))
        # Applicants round up: actual activity runs a little below the stated figure on average.
        actual = stated * float(lognormal_around(rng, 0.9, 0.25))
        if rng.random() < pop["share_open_before_window"]:
            open_day = -int(rng.uniform(cfg["window"]["warmup_days"], pop["max_years_open_before_window"] * 365))
        else:
            open_day = int(rng.uniform(0, cal.n_days - 30))
        out.append(Business(
            business_id=i + 1,
            industry=ind,
            stated_revenue=round(stated, -2),
            actual_revenue=actual,
            growth_per_year=float(rng.normal(0.04, 0.10)),
            open_day=open_day,
            incorporation_day=open_day - int(lognormal_around(rng, 4 * 365, 0.9)),
            state=STATES[rng.integers(len(STATES))],
            has_payroll=bool(rng.random() < icfg["has_payroll"]),
            has_tax_account=bool(rng.random() < 0.6),
        ))
    _assign_archetypes(cfg, rng, out)
    _assign_fraud(cfg, rng, cal, out)
    return out


def _assign_archetypes(cfg: dict, rng: np.random.Generator, businesses: list[Business]) -> None:
    for name, a in cfg["odd_archetypes"].items():
        for b in businesses:
            if b.archetype == "standard" and b.industry in a["industries"] and rng.random() < a["share"]:
                b.archetype = name


def _assign_fraud(cfg: dict, rng: np.random.Generator, cal: Calendar, businesses: list[Business]) -> None:
    n = len(businesses)
    order = rng.permutation(n)
    taken: set[int] = set()
    for typ, t in cfg["typologies"].items():
        k = int(round(t["prevalence"] * n))
        chosen = [i for i in order if i not in taken][:k]
        taken.update(chosen)
        for i in chosen:
            b = businesses[i]
            b.fraud = typ
            b.fraud_variant = pick(rng, t["variants"])
            if typ == "check_deposit_fraud":
                _setup_check_fraud(t, rng, cal, b)
            else:
                # BEC victims are good, established customers; the scheme needs payment history to imitate.
                b.archetype = "standard"
                b.open_day = min(b.open_day, -cfg["window"]["warmup_days"])
                b.extra["case_day"] = int(rng.uniform(30, cal.n_days - 35))
        order = rng.permutation(n)


def _setup_check_fraud(t: dict, rng: np.random.Generator, cal: Calendar, b: Business) -> None:
    b.archetype = "standard"
    if rng.random() < t["share_new_account"]:
        # Opened for the purpose: a small business, inside the window, schemed within weeks.
        b.extra["new_account"] = True
        b.stated_revenue = round(float(rng.uniform(8_000, 40_000)), -2)
        b.actual_revenue = b.stated_revenue * float(rng.uniform(0.2, 0.5))
        b.open_day = int(rng.uniform(0, cal.n_days - 100))
        b.incorporation_day = b.open_day - int(rng.uniform(10, 400))
        b.has_payroll = bool(rng.random() < 0.2)
        lo, hi = t["new_account_scheme_after_days"]
        b.extra["case_day"] = b.open_day + int(rng.uniform(lo, hi))
    else:
        # An existing customer turning to deposit fraud (first-party): years of normal history first.
        b.extra["new_account"] = False
        b.extra["case_day"] = int(rng.uniform(30, cal.n_days - 15))


def build_owners(cfg: dict, businesses: list[Business]) -> list[dict]:
    fake = Faker("en_US")
    fake.seed_instance(cfg["seed"])
    rng = rng_for(cfg["seed"], "owners")
    rows = []
    for b in businesses:
        for k in range(1 if rng.random() < 0.75 else 2):
            first, last = fake.first_name(), fake.last_name()
            rows.append({
                "owner_id": b.business_id * 10 + k,
                "business_id": b.business_id,
                "full_name": f"{first} {last}",
                "email": f"{first.lower()}.{last.lower()}{rng.integers(10, 99)}@{fake.free_email_domain()}",
                "phone": f"555-{rng.integers(100, 999)}-{rng.integers(1000, 9999)}",   # 555: never a real number
                "address": fake.street_address(),
                "state": b.state,
                "device_id": f"dev-{rng.integers(16**10):010x}",
            })
    return rows


def business_rows(cal: Calendar, businesses: list[Business]) -> list[dict]:
    fake = Faker("en_US")
    fake.seed_instance(4242)
    rows = []
    for b in businesses:
        rows.append({
            "business_id": b.business_id,
            "legal_name": f"{fake.last_name()} {fake.random_element(['Group', 'Works', 'Supply', 'Studio', 'Partners', 'Co', 'Services', 'Collective'])} LLC",
            "industry": b.industry,
            "size_band": b.size_band,
            "incorporation_date": cal.start + dt.timedelta(days=b.incorporation_day),
            "state": b.state,
            "stated_monthly_revenue": b.stated_revenue,
        })
    return rows


def account_rows(cal: Calendar, businesses: list[Business]) -> list[dict]:
    rows = []
    for b in businesses:
        for acc in b.account_ids():
            sub = acc % 10
            # Sub-accounts open a few days after the operating account.
            rows.append({
                "account_id": acc,
                "business_id": b.business_id,
                "account_type": SUB_ACCOUNTS[sub],
                "open_date": cal.start + dt.timedelta(days=b.open_day + (0 if sub == 0 else 3)),
            })
    return rows


def first_activity_day(cal: Calendar, b: Business) -> int:
    return max(b.open_day, cal.first_day)


def to_seconds(day: int) -> int:
    return day * DAY
