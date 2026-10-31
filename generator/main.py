"""Generate the synthetic bank: raw files in data/raw/, the answer key in data/answer_key/.

  uv run python -m generator.main [--n-businesses N] [--out DIR]

Raw files are what the bank would see. The answer key (which cases are fraud, which transactions belong to them,
and each business's hidden archetype) is written separately and is read only by the backtest grader.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from generator import events, legit
from generator.common import DAY, EVENT_SCHEMA, INBOUND, ROOT, TXN_SCHEMA, Calendar, Columns, load_config, rng_for
from generator.typologies import (account_takeover, ach_return_fraud, bec_vendor_change, check_deposit_fraud,
                                  money_mule, synthetic_shell)
from generator.world import account_rows, build_businesses, build_identities, business_rows

TYPOLOGIES = {"check_deposit_fraud": check_deposit_fraud, "bec_vendor_change": bec_vendor_change,
              "synthetic_shell": synthetic_shell, "money_mule": money_mule,
              "account_takeover": account_takeover, "ach_return_fraud": ach_return_fraud}


def _ts(cal: Calendar, seconds: np.ndarray) -> pa.Array:
    base = np.datetime64(cal.start.isoformat(), "s")
    return pa.array(base + seconds.astype("timedelta64[s]"))


def _write(rows: list[dict] | dict, path: Path) -> None:
    table = pa.Table.from_pylist(rows) if isinstance(rows, list) else pa.table(rows)
    pq.write_table(table, path)


def generate(cfg: dict, out: Path) -> dict:
    cal = Calendar.from_config(cfg)
    businesses = build_businesses(cfg, cal)
    owners, applications = build_identities(cfg, cal, businesses)
    payees = legit.Payees()
    ev = Columns(EVENT_SCHEMA)
    parts, cases = [], []
    case_id = 0
    for b in businesses:
        if b.fraud:
            TYPOLOGIES[b.fraud].plan(cfg, b)
        buf = Columns(TXN_SCHEMA)
        ctx = legit.generate(cfg, cal, b, rng_for(cfg["seed"], "legit", b.business_id), buf, payees)
        events.generate(cfg, cal, b, rng_for(cfg["seed"], "events", b.business_id), ev, ctx)
        if b.fraud:
            case_id += 1
            frng = rng_for(cfg["seed"], b.fraud, b.business_id)
            if b.fraud == "bec_vendor_change":
                # BEC rewrites the victim's own payment history, so it works on the finished arrays.
                tx, case = bec_vendor_change.plant(cfg, cal, b, frng, buf.finish(), payees, ctx, case_id)
                buf = None
            elif b.fraud == "account_takeover":
                case = account_takeover.plant(cfg, cal, b, frng, buf, payees, ev, case_id)
            else:
                case = TYPOLOGIES[b.fraud].plant(cfg, cal, b, frng, buf, payees, case_id)
            if case:
                cases.append(case)
            else:
                b.fraud = None
        parts.append(buf.finish() if buf is not None else tx)

    tx = {c: np.concatenate([p[c] for p in parts if len(p[c])]) for c in TXN_SCHEMA}
    # Stable transaction ids: by time, then business, then account, then amount.
    order = np.lexsort((tx["amount"], tx["account_id"], tx["business_id"], tx["t"]))
    tx = {c: v[order] for c, v in tx.items()}
    n = len(tx["t"])
    txn_id = np.arange(1, n + 1, dtype=np.int64)

    # Payee bank details in force at payment time: the latest created/changed event at or before it.
    pev = np.array([(p, t, v) for p, t, _, v in payees.events], dtype=np.int64)
    pev = pev[np.lexsort((pev[:, 1], pev[:, 0]))]
    details = np.full(n, -1, dtype=np.int64)
    has_payee = tx["payee_id"] >= 0
    # Exact integer key (payee, time): times are shifted positive and fit in 29 bits, payee ids in 24.
    key = lambda payee, t: payee.astype(np.int64) * 2**29 + (t.astype(np.int64) + 2 * 10**8)
    key_ev = key(pev[:, 0], pev[:, 1])
    key_tx = key(tx["payee_id"][has_payee], tx["t"][has_payee])
    idx = np.searchsorted(key_ev, key_tx, side="right") - 1
    ok = (idx >= 0) & (pev[np.clip(idx, 0, None), 0] == tx["payee_id"][has_payee])
    d = np.where(ok, pev[np.clip(idx, 0, None), 0] * 100 + pev[np.clip(idx, 0, None), 2], -1)
    details[has_payee] = d

    out.mkdir(parents=True, exist_ok=True)
    raw, key = out / "raw", out / "answer_key"
    for folder in (raw, key):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)

    _write(business_rows(cal, businesses), raw / "businesses.parquet")
    _write(owners, raw / "owners.parquet")
    _write({
        "application_id": [a["application_id"] for a in applications],
        "business_id": pa.array([a["business_id"] for a in applications], type=pa.int64()),
        "applied_at": _ts(cal, np.array([a["applied_t"] for a in applications])),
        "decision": [a["decision"] for a in applications],
        "industry": [a["industry"] for a in applications],
        "stated_monthly_revenue": [a["stated_monthly_revenue"] for a in applications],
        "incorporation_date": [cal.start + dt.timedelta(days=a["incorporation_day"]) for a in applications],
        "state": [a["state"] for a in applications],
        "applicant_name": [a["applicant_name"] for a in applications],
        "email": [a["email"] for a in applications],
        "phone": [a["phone"] for a in applications],
        "address": [a["address"] for a in applications],
        "device_id": [a["device_id"] for a in applications],
    }, raw / "applications.parquet")
    e = ev.finish()
    eo = np.lexsort((e["event_type"].astype(str), e["business_id"], e["t"]))
    _write({"event_id": np.arange(1, len(eo) + 1), "business_id": e["business_id"][eo].astype(np.int64),
            "owner_id": e["owner_id"][eo].astype(np.int64), "event_time": _ts(cal, e["t"][eo]),
            "event_type": e["event_type"][eo].astype(str), "device_id": e["device_id"][eo].astype(str)},
           raw / "events.parquet")
    _write(account_rows(cal, businesses), raw / "accounts.parquet")
    pay = sorted(payees.rows, key=lambda r: r["payee_id"])
    _write({"payee_id": [r["payee_id"] for r in pay], "business_id": [r["business_id"] for r in pay],
            "payee_type": [r["payee_type"] for r in pay], "payee_name": [r["payee_name"] for r in pay],
            "created_at": _ts(cal, np.array([r["created_t"] for r in pay]))}, raw / "payees.parquet")
    pe = sorted(payees.events, key=lambda e: (e[0], e[1]))
    _write({"payee_event_id": np.arange(1, len(pe) + 1), "payee_id": [e[0] for e in pe],
            "event_time": _ts(cal, np.array([e[1] for e in pe])), "event_type": [e[2] for e in pe],
            "bank_details_id": [e[0] * 100 + e[3] for e in pe]}, raw / "payee_events.parquet")

    inbound = np.isin(tx["txn_type"], list(INBOUND))
    _write({
        "txn_id": txn_id,
        "account_id": tx["account_id"].astype(np.int64),
        "business_id": tx["business_id"].astype(np.int64),
        "txn_time": _ts(cal, tx["t"]),
        "txn_type": tx["txn_type"].astype(str),
        "direction": np.where(inbound, "in", "out"),
        "amount": tx["amount"].astype(np.float64),
        "counterparty_id": pa.array(np.where(tx["counterparty_id"] >= 0, tx["counterparty_id"], 0), mask=tx["counterparty_id"] < 0),
        "payee_id": pa.array(tx["payee_id"], mask=tx["payee_id"] < 0),
        "bank_details_id": pa.array(details, mask=details < 0),
    }, raw / "transactions.parquet")

    r = tx["return_after_s"] >= 0
    _write({"return_id": np.arange(1, r.sum() + 1), "txn_id": txn_id[r],
            "return_time": _ts(cal, tx["t"][r] + tx["return_after_s"][r]),
            "return_reason": tx["return_reason"][r].astype(str)}, raw / "returns.parquet")

    # ---- answer key: never read by features or rules ----
    c = tx["case_id"] >= 0
    _write({"txn_id": txn_id[c], "case_id": tx["case_id"][c].astype(np.int64),
            "role": tx["role"][c].astype(str), "loss_amount": tx["loss_amount"][c]}, key / "fraud_txns.parquet")
    # When the bank learns each case was fraud (ADR-013): some delay after the case ends; some never.
    known = []
    for k in cases:
        tcfg = cfg["typologies"][k["typology"]]
        lrng = rng_for(cfg["seed"], "labels", k["business_id"])
        delay = lrng.uniform(*tcfg["label_delay_days"]) * DAY
        known.append(None if lrng.random() < tcfg["never_labelled"] else int(k["case_end_t"] + delay))
    known_arr = np.array([0 if x is None else x for x in known], dtype=np.int64)
    _write({
        "case_id": [k["case_id"] for k in cases], "business_id": [k["business_id"] for k in cases],
        "ring_id": pa.array([k.get("ring_id") for k in cases], type=pa.int64()),
        "label_known_at": pa.array(np.datetime64(cal.start.isoformat(), "s") + known_arr.astype("timedelta64[s]"),
                                   mask=np.array([x is None for x in known])),
        "typology": [k["typology"] for k in cases], "variant": [k["variant"] for k in cases],
        "account_is_fraudulent": [k["account_is_fraudulent"] for k in cases],
        "case_start": _ts(cal, np.array([k["case_start_t"] for k in cases])),
        "case_end": _ts(cal, np.array([k["case_end_t"] for k in cases])),
        "loss_if_uncaught": [round(k["loss_if_uncaught"], 2) for k in cases],
    }, key / "fraud_cases.parquet")
    _write([{"business_id": b.business_id, "archetype": b.archetype} for b in businesses], key / "business_profile.parquet")
    return {"businesses": len(businesses), "transactions": n, "cases": len(cases), "payees": len(pay),
            "applications": len(applications), "events": len(eo)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-businesses", type=int)
    ap.add_argument("--out", type=Path, default=ROOT / "data")
    args = ap.parse_args()
    cfg = load_config()
    if args.n_businesses:
        cfg["population"]["n_businesses"] = args.n_businesses
    t0 = time.time()
    stats = generate(cfg, args.out)
    print(f"generated {stats} in {time.time() - t0:.1f}s -> {args.out}")


if __name__ == "__main__":
    main()
