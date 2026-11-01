"""Responses from three invented external data vendors (module D, ADR-022). Parameters: config/vendors.yaml.

Each vendor answers at its call points (applications, new-device logins, contact changes) with a 0-100 risk
score, or no answer when the entity isn't covered. Scores are drawn from the planted truth with noise, so a
vendor knows something the bank doesn't, but imperfectly. Every call point gets a response here; the backtest
decides which ones each call strategy would actually pay for.
"""
from __future__ import annotations

import numpy as np

from generator.common import ROOT, rng_for

FREE_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com"}
FIRST_PARTY_NEW = {"check_deposit_fraud", "money_mule", "ach_return_fraud"}


def load() -> dict:
    import yaml
    return yaml.safe_load((ROOT / "config" / "vendors.yaml").read_text())


def _bad_business(b) -> bool:
    return b.fraud == "synthetic_shell" or (b.fraud in FIRST_PARTY_NEW and b.extra.get("new_account", False))


def _scores(rng, bad: np.ndarray, sig: dict, bump: np.ndarray | None = None) -> np.ndarray:
    mean = np.where(bad, sig["bad_mean"], sig["good_mean"]) + (0 if bump is None else bump)
    return np.clip(np.round(rng.normal(mean, sig["sd"])), 0, 100)


def call_points(applications: list[dict], businesses: list, events: dict) -> dict:
    """The entities each vendor can be asked about, with the truth its signal is drawn from."""
    by_id = {b.business_id: b for b in businesses}
    apps = {
        "call_point_id": np.array([a["application_id"] for a in applications], dtype=np.int64),
        "business_id": np.array([a["business_id"] or -1 for a in applications], dtype=np.int64),
        "t": np.array([a["applied_t"] for a in applications], dtype=np.int64),
        "bad": np.array([a["ring"] or (a["business_id"] is not None and _bad_business(by_id[a["business_id"]]))
                         for a in applications]),
        "device_id": np.array([a["device_id"] for a in applications], dtype=object),
        "business_domain": np.array([a["email"].split("@")[1] not in FREE_DOMAINS for a in applications]),
    }
    # A new-device login is a device's first login on a business.
    e = events
    is_login = e["event_type"] == "login"
    seen, first = set(), np.zeros(len(e["t"]), dtype=bool)
    for i in np.flatnonzero(is_login):
        key = (int(e["business_id"][i]), e["device_id"][i])
        if key not in seen:
            seen.add(key)
            first[i] = True
    fraud_business = np.array([_bad_business(by_id[int(b)]) for b in e["business_id"]])
    logins = np.flatnonzero(first)
    changes = np.flatnonzero(np.isin(e["event_type"], ["email_changed", "phone_changed"]))
    return {
        "application": apps,
        "new_device_login": {"call_point_id": e["event_id"][logins], "business_id": e["business_id"][logins],
                             "t": e["t"][logins], "bad": e["is_fraud"][logins] | fraud_business[logins]},
        "contact_change": {"call_point_id": e["event_id"][changes], "business_id": e["business_id"][changes],
                           "t": e["t"][changes], "bad": e["is_fraud"][changes]},
    }


def responses(seed: int, points: dict) -> dict[str, dict]:
    """vendor key -> columns of its response table."""
    cfg = load()["vendors"]
    out = {}
    for key, v in cfg.items():
        rng = rng_for(seed, "vendors", list(cfg).index(key))
        cols = {k: [] for k in ("call_point", "call_point_id", "business_id", "t", "covered", "score", "result", "latency_ms")}
        for cp in v["call_points"]:
            p = points[cp]
            n = len(p["t"])
            covered = rng.random(n) < v["coverage"]
            if key == "larchstone":
                fail = rng.random(n) < np.where(p["bad"], v["fail_rate_bad"], v["fail_rate_good"])
                result = np.where(fail, np.where(rng.random(n) < 0.5, "not_found", "mismatch"), "verified").astype(object)
                score = np.where(fail, 90.0, 10.0)
            else:
                bump = None
                if cp == "application" and key == "tallowmere":
                    devices, counts = np.unique(p["device_id"], return_counts=True)
                    shared = dict(zip(devices, counts))
                    bump = np.array([v["shared_device_bump"] if shared[d] >= 5 else 0 for d in p["device_id"]])
                if cp == "application" and key == "quenchwire":
                    bump = np.where(p["business_domain"], v["business_domain_bump"], 0)
                score = _scores(rng, p["bad"], v["signal"], bump)
                result = np.full(n, "", dtype=object)
            cols["call_point"].append(np.full(n, cp, dtype=object))
            cols["call_point_id"].append(p["call_point_id"])
            cols["business_id"].append(p["business_id"])
            cols["t"].append(p["t"])
            cols["covered"].append(covered)
            cols["score"].append(np.where(covered, score, np.nan))
            cols["result"].append(np.where(covered, result, "").astype(object))
            cols["latency_ms"].append(np.round(v["latency_ms"] * np.exp(rng.normal(0, 0.3, n))))
        out[key] = {k: np.concatenate(vals) for k, vals in cols.items()}
    return out
