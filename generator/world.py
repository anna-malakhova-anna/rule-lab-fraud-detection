"""Businesses, owners and accounts, plus which businesses get an odd-but-legitimate archetype or a fraud case.

Assignments are drawn here, before any activity, so each activity generator knows how a business behaves.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
from faker import Faker

from generator.common import APPLICATION_ID_BASE, DAY, Calendar, lognormal_around, pick, rng_for

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
            b.archetype = "standard"
            SETUP[typ](cfg, t, rng, cal, b)
        if typ == "synthetic_shell":
            _form_rings(t, rng, [businesses[i] for i in chosen], cal)
        order = rng.permutation(n)


def _established(cfg: dict, b: Business) -> None:
    b.open_day = min(b.open_day, -cfg["window"]["warmup_days"])


def _setup_bec(cfg, t, rng, cal, b) -> None:
    # BEC victims are good, established customers; the scheme needs payment history to imitate.
    _established(cfg, b)
    b.extra["case_day"] = int(rng.uniform(30, cal.n_days - 35))


def _setup_shell(cfg, t, rng, cal, b) -> None:
    # A synthetic or shell business: freshly incorporated, big stated revenue, little real activity.
    b.open_day = int(rng.uniform(0, cal.n_days - 90))
    b.incorporation_day = b.open_day - int(rng.uniform(*t["incorporated_days_before"]))
    b.stated_revenue = round(float(rng.uniform(*t["stated_revenue"])), -2)
    b.actual_revenue = float(rng.uniform(2_000, 8_000))
    b.has_payroll = False
    b.extra["new_account"] = True
    b.extra["case_day"] = b.open_day + int(rng.uniform(*t["bust_after_days"]))


def _form_rings(t: dict, rng: np.random.Generator, shells: list[Business], cal: Calendar) -> None:
    """Group shells into rings that share devices, phones, an address and an email domain.
    Ring start dates are spread evenly over the window so both the tuning and test months see rings."""
    sizes, left = [], len(shells)
    while left > 0:
        sizes.append(min(left, int(rng.integers(t["ring_size"][0], t["ring_size"][1] + 1))))
        left -= sizes[-1]
    i = 0
    for ring_id, size in enumerate(sizes, start=1):
        anchor = int((ring_id - 1 + rng.uniform(0, 1)) / len(sizes) * (cal.n_days - 90))
        for m in shells[i:i + size]:
            m.extra["ring_id"] = ring_id
            # Ring members apply within a few weeks of each other.
            m.open_day = anchor + int(rng.uniform(0, 30))
            m.incorporation_day = m.open_day - int(rng.uniform(*t["incorporated_days_before"]))
            m.extra["case_day"] = m.open_day + int(rng.uniform(*t["bust_after_days"]))
        i += size


def _setup_mule(cfg, t, rng, cal, b) -> None:
    if b.fraud_variant == "opened_for_purpose":
        b.open_day = int(rng.uniform(0, cal.n_days - 80))
        b.actual_revenue = float(rng.uniform(1_500, 6_000))
        b.has_payroll = False
        b.extra["new_account"] = True
        b.extra["case_day"] = b.open_day + int(rng.uniform(*t["start_after_open_days"]))
    else:
        # An existing small business that lets its account be used.
        b.extra["new_account"] = False
        b.extra["case_day"] = int(rng.uniform(30, cal.n_days - 45))


def _setup_ato(cfg, t, rng, cal, b) -> None:
    _established(cfg, b)
    b.extra["case_day"] = int(rng.uniform(15, cal.n_days - 10))


def _setup_ach_return(cfg, t, rng, cal, b) -> None:
    start = int(np.searchsorted(cal.month_ordinal, t["starts_month"] - 1)) + cal.first_day   # first day of that month
    if b.fraud_variant == "newer_account":
        b.extra["new_account"] = True
        b.open_day = start - int(rng.uniform(30, 180))
    else:
        b.extra["new_account"] = False
        _established(cfg, b)
    b.extra["case_day"] = int(rng.uniform(start, cal.n_days - 16))


def _setup_check_fraud(cfg, t, rng, cal, b) -> None:
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


def _setup_bust_out(cfg, t, rng, cal, b) -> None:
    # An established customer: the scheme needs a line, so the account is at least ~7 months old by the time
    # the window opens and qualifies for a line from day one (generator/credit.py).
    _established(cfg, b)
    b.open_day = min(b.open_day, -210)
    b.extra["case_day"] = int(rng.uniform(60, cal.n_days - 45))


SETUP = {
    "check_deposit_fraud": _setup_check_fraud,
    "bec_vendor_change": _setup_bec,
    "synthetic_shell": _setup_shell,
    "money_mule": _setup_mule,
    "account_takeover": _setup_ato,
    "ach_return_fraud": _setup_ach_return,
    "credit_bust_out": _setup_bust_out,
}


def _person(fake: Faker, rng: np.random.Generator, bid: int, business_domain: bool) -> dict:
    first, last = fake.first_name(), fake.last_name()
    domain = f"{last.lower()}{bid}.example" if business_domain else fake.free_email_domain()
    return {
        "full_name": f"{first} {last}",
        "email": f"{first.lower()}.{last.lower()}{rng.integers(10, 99)}@{domain}",
        "phone": f"555-{rng.integers(100, 999)}-{rng.integers(1000, 9999)}",   # 555: never a real number
        "address": fake.street_address(),
        "device_id": f"dev-{rng.integers(16**10):010x}",
    }


def build_identities(cfg: dict, cal: Calendar, businesses: list[Business]) -> tuple[list[dict], list[dict]]:
    """Owners (what the bank holds on file) and onboarding applications, approved and declined.

    Legitimate sharing is planted on purpose: an owner with two businesses, applicants who apply through
    their bookkeeper's device, tenants of the same co-working address. Shell rings share devices, phones,
    an address and an email domain. Returns (owners, applications).
    """
    fake = Faker("en_US")
    fake.seed_instance(cfg["seed"])
    rng = rng_for(cfg["seed"], "identity")
    sh, ap = cfg["shared_identity"], cfg["applications"]
    n = len(businesses)
    bookkeepers = [f"dev-bk{k:04d}" for k in range(max(1, int(n * sh["bookkeeper_share"] / np.mean(sh["bookkeeper_clients"]))))]
    coworking = [f"{100 + k} Commerce Hub, Suite {k}" for k in range(max(1, int(n * sh["coworking_share"] / np.mean(sh["coworking_tenants"]))))]

    rings: dict[int, dict] = {}
    primary: dict[int, dict] = {}
    owners, apps = [], []
    for b in businesses:
        ring = b.extra.get("ring_id")
        if ring is not None:
            if ring not in rings:
                rings[ring] = {"devices": [f"dev-{rng.integers(16**10):010x}" for _ in range(2)],
                               "phones": [f"555-{rng.integers(100, 999)}-{rng.integers(1000, 9999)}" for _ in range(2)],
                               "address": fake.street_address(), "domain": f"{fake.last_name().lower()}-ventures{ring}.example"}
            r = rings[ring]
            first, last = fake.first_name(), fake.last_name()
            person = {"full_name": f"{first} {last}", "email": f"{first.lower()}.{last.lower()}@{r['domain']}",
                      "phone": r["phones"][rng.integers(2)], "address": r["address"], "device_id": r["devices"][rng.integers(2)]}
        elif b.business_id > 1 and rng.random() < sh["sibling_share"]:
            person = dict(primary[int(rng.integers(1, b.business_id))])   # same owner, second business
        else:
            person = _person(fake, rng, b.business_id, rng.random() < sh["business_email_domain_share"])
        primary[b.business_id] = person
        address = person["address"]
        if ring is None and rng.random() < sh["coworking_share"]:
            address = coworking[rng.integers(len(coworking))]
        apply_device = person["device_id"]
        if ring is None and rng.random() < sh["bookkeeper_share"]:
            apply_device = bookkeepers[rng.integers(len(bookkeepers))]
        b.extra["owner_device"] = person["device_id"]
        owners.append({"owner_id": b.business_id * 10, "business_id": b.business_id, "state": b.state, **person,
                       "address": address})
        if rng.random() < 0.25 and ring is None:
            owners.append({"owner_id": b.business_id * 10 + 1, "business_id": b.business_id, "state": b.state,
                           **_person(fake, rng, b.business_id, False)})
        applied = (b.open_day - rng.uniform(*ap["days_before_open"])) * DAY
        apps.append(_application(b.business_id, applied, "approved", b.industry, b.stated_revenue,
                                 b.incorporation_day, b.state, person, address, apply_device))

    # Declined applications: ordinary applicants the bank's existing checks turned down, plus ring attempts.
    names = list(cfg["industries"])
    for k in range(int(n * ap["declined_share"])):
        person = _person(fake, rng, 900_000 + k, rng.random() < sh["business_email_domain_share"])
        address = coworking[rng.integers(len(coworking))] if rng.random() < sh["coworking_share"] else person["address"]
        device = bookkeepers[rng.integers(len(bookkeepers))] if rng.random() < sh["bookkeeper_share"] else person["device_id"]
        day = rng.uniform(cal.first_day - 365, cal.n_days)
        apps.append(_application(None, day * DAY, "declined", names[rng.integers(len(names))],
                                 round(float(rng.uniform(5_000, 150_000)), -2), int(day - rng.uniform(5, 2000)),
                                 STATES[rng.integers(len(STATES))], person, address, device))
    t = cfg["typologies"]["synthetic_shell"]
    for ring, r in rings.items():
        members = [b for b in businesses if b.extra.get("ring_id") == ring]
        anchor = min(m.open_day for m in members)
        for _ in range(int(rng.integers(t["extra_declined_per_ring"][0], t["extra_declined_per_ring"][1] + 1))):
            first, last = fake.first_name(), fake.last_name()
            person = {"full_name": f"{first} {last}", "email": f"{first.lower()}.{last.lower()}@{r['domain']}",
                      "phone": r["phones"][rng.integers(2)], "address": r["address"], "device_id": r["devices"][rng.integers(2)]}
            day = anchor - rng.uniform(1, 20)
            apps.append(_application(None, day * DAY, "declined", names[rng.integers(len(names))],
                                     round(float(rng.uniform(*t["stated_revenue"])), -2), int(day - rng.uniform(5, 60)),
                                     STATES[rng.integers(len(STATES))], person, person["address"], person["device_id"]))
    apps.sort(key=lambda a: (a["applied_t"], a["business_id"] or 0, a["email"]))
    for i, a in enumerate(apps):
        a["application_id"] = APPLICATION_ID_BASE + i + 1
    return owners, apps


def _application(bid, applied_t, decision, industry, revenue, inc_day, state, person, address, device) -> dict:
    return {"business_id": bid, "applied_t": int(applied_t), "decision": decision, "industry": industry,
            "stated_monthly_revenue": revenue, "incorporation_day": inc_day, "state": state,
            "applicant_name": person["full_name"], "email": person["email"], "phone": person["phone"],
            "address": address, "device_id": device}


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
