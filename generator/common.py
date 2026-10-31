"""Shared pieces for the generator: config, calendar, random streams and a columnar buffer.

Time is carried as integer seconds from the window start (negative = warm-up). It becomes a timestamp only
when files are written, so the generator never touches time zones or daylight saving.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
DAY = 86_400
HOUR = 3_600

# Independent random streams: adding a typology never changes the legitimate world's draws.
STREAMS = {"world": 1, "legit": 2, "check_deposit_fraud": 3, "bec_vendor_change": 4, "owners": 5,
           "synthetic_shell": 6, "money_mule": 7, "account_takeover": 8, "ach_return_fraud": 9,
           "events": 10, "applications": 11, "labels": 12, "identity": 13}


def load_config(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "config" / "generation.yaml").read_text())


def rng_for(seed: int, stream: str, *keys: int) -> np.random.Generator:
    return np.random.default_rng([seed, STREAMS[stream], *keys])


@dataclass(frozen=True)
class Calendar:
    """Day-indexed calendar from the start of the warm-up to the end of the window."""
    start: dt.date
    first_day: int          # negative: the warm-up
    n_days: int             # days in the window
    month: np.ndarray       # calendar month 0..11, indexed by day - first_day
    month_ordinal: np.ndarray  # months since window start (warm-up is negative)
    dow: np.ndarray         # 0 = Monday

    @classmethod
    def from_config(cls, cfg: dict) -> "Calendar":
        w = cfg["window"]
        start = dt.date.fromisoformat(w["start_date"])
        y, m = divmod(start.month - 1 + w["months"], 12)
        end = dt.date(start.year + y, m + 1, 1)
        n_days = (end - start).days
        first = -int(w["warmup_days"])
        dates = [start + dt.timedelta(days=d) for d in range(first, n_days)]
        return cls(
            start=start,
            first_day=first,
            n_days=n_days,
            month=np.array([d.month - 1 for d in dates]),
            month_ordinal=np.array([(d.year - start.year) * 12 + d.month - start.month for d in dates]),
            dow=np.array([d.weekday() for d in dates]),
        )

    def days(self, lo: int, hi: int) -> np.ndarray:
        """Day indexes in [lo, hi), clipped to the calendar."""
        lo, hi = max(lo, self.first_day), min(hi, self.n_days)
        return np.arange(lo, hi) if hi > lo else np.arange(0)

    def at(self, arr: np.ndarray, days: np.ndarray) -> np.ndarray:
        return arr[days - self.first_day]

    def business_days(self, lo: int, hi: int) -> np.ndarray:
        d = self.days(lo, hi)
        return d[self.at(self.dow, d) < 5]

    def next_business_day(self, days: np.ndarray) -> np.ndarray:
        d = np.clip(days, self.first_day, self.n_days - 1)
        dow = self.at(self.dow, d)
        return d + np.where(dow == 5, 2, np.where(dow == 6, 1, 0))


def times_on(rng: np.random.Generator, days: np.ndarray, start_hour: float = 8, end_hour: float = 19) -> np.ndarray:
    """A random second within business hours on each given day."""
    return days.astype(np.int64) * DAY + (rng.uniform(start_hour, end_hour, len(days)) * HOUR).astype(np.int64)


def lognormal_around(rng: np.random.Generator, median, sigma: float, size=None) -> np.ndarray:
    return np.asarray(median) * np.exp(rng.normal(0.0, sigma, size))


def pick(rng: np.random.Generator, weights: dict) -> str:
    keys = list(weights)
    p = np.array([weights[k] for k in keys], dtype=float)
    return keys[rng.choice(len(keys), p=p / p.sum())]


class Columns:
    """Append-only columnar buffer: append arrays, concatenate once at the end."""

    def __init__(self, schema: dict[str, object]):
        self.schema = schema              # column -> fill value used when an append omits the column
        self.parts: dict[str, list] = {c: [] for c in schema}

    def append(self, **cols) -> None:
        n = max(len(v) for v in cols.values() if np.ndim(v))
        if n == 0:
            return
        for c, fill in self.schema.items():
            v = cols.get(c, fill)
            dtype = object if isinstance(fill, str) else None    # object strings: no silent truncation on concat
            self.parts[c].append(np.asarray(v, dtype=dtype) if np.ndim(v) else np.full(n, v, dtype=dtype))

    def finish(self) -> dict[str, np.ndarray]:
        return {c: (np.concatenate(p) if p else np.array([])) for c, p in self.parts.items()}


# Internal transaction columns. case_id/role/loss_amount and the return columns are split off when files are
# written: the case columns go to the answer key, the return columns become the returns table.
TXN_SCHEMA = {
    "business_id": -1, "account_id": -1, "t": 0, "txn_type": "", "amount": 0.0,
    "counterparty_id": -1, "payee_id": -1,
    "return_after_s": -1, "return_reason": "",
    "case_id": -1, "role": "", "loss_amount": 0.0,
}
INBOUND = {"card_settlement", "ach_in", "ach_debit_in", "wire_in", "mobile_check_deposit", "internal_transfer_in"}
EVENT_SCHEMA = {"business_id": -1, "owner_id": -1, "t": 0, "event_type": "", "device_id": ""}
APPLICATION_ID_BASE = 10**12   # application ids never collide with transaction ids (both are rule entity ids)
