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

from generator import legit
from generator.common import DAY, INBOUND, ROOT, TXN_SCHEMA, Calendar, Columns, load_config, rng_for
from generator.typologies import bec_vendor_change, check_deposit_fraud
from generator.world import account_rows, build_businesses, build_owners, business_rows

TYPOLOGIES = {"check_deposit_fraud": check_deposit_fraud, "bec_vendor_change": bec_vendor_change}


def _ts(cal: Calendar, seconds: np.ndarray) -> pa.Array:
    base = np.datetime64(cal.start.isoformat(), "s")
    return pa.array(base + seconds.astype("timedelta64[s]"))


def _write(rows: list[dict] | dict, path: Path) -> None:
    table = pa.Table.from_pylist(rows) if isinstance(rows, list) else pa.table(rows)
    pq.write_table(table, path)


def generate(cfg: dict, out: Path) -> dict:
    cal = Calendar.from_config(cfg)
    businesses = build_businesses(cfg, cal)
    payees = legit.Payees()
    parts, cases = [], []
    case_id = 0
    for b in businesses:
        if b.fraud:
            TYPOLOGIES[b.fraud].plan(cfg, b)
        buf = Columns(TXN_SCHEMA)
        ctx = legit.generate(cfg, cal, b, rng_for(cfg["seed"], "legit", b.business_id), buf, payees)
        tx = buf.finish()
        if b.fraud:
            case_id += 1
            frng = rng_for(cfg["seed"], b.fraud, b.business_id)
            if b.fraud == "check_deposit_fraud":
                fbuf = Columns(TXN_SCHEMA)
                cases.append(check_deposit_fraud.plant(cfg, cal, b, frng, fbuf, payees, case_id))
                f = fbuf.finish()
                tx = {c: np.concatenate([tx[c], f[c]]) for c in tx}
            else:
                tx, case = bec_vendor_change.plant(cfg, cal, b, frng, tx, payees, ctx, case_id)
                if case:
                    cases.append(case)
                else:
                    b.fraud = None
        parts.append(tx)

    tx = {c: np.concatenate([p[c] for p in parts if len(p[c])]) for c in TXN_SCHEMA}
    # Stable transaction ids: by time, then business, then account, then amount.
    order = np.lexsort((tx["amount"], tx["account_id"], tx["business_id"], tx["t"]))
    tx = {c: v[order] for c, v in tx.items()}
    n = len(tx["t"])
    txn_id = np.arange(1, n + 1, dtype=np.int64)

    # Payee bank details in force at payment time: the latest created/changed event at or before it.
    ev = np.array([(p, t, v) for p, t, _, v in payees.events], dtype=np.int64)
    ev = ev[np.lexsort((ev[:, 1], ev[:, 0]))]
    details = np.full(n, -1, dtype=np.int64)
    has_payee = tx["payee_id"] >= 0
    key_ev = ev[:, 0].astype(np.float64) * 1e12 + ev[:, 1]
    key_tx = tx["payee_id"][has_payee].astype(np.float64) * 1e12 + tx["t"][has_payee]
    idx = np.searchsorted(key_ev, key_tx, side="right") - 1
    ok = (idx >= 0) & (ev[np.clip(idx, 0, None), 0] == tx["payee_id"][has_payee])
    d = np.where(ok, ev[np.clip(idx, 0, None), 0] * 100 + ev[np.clip(idx, 0, None), 2], -1)
    details[has_payee] = d

    out.mkdir(parents=True, exist_ok=True)
    raw, key = out / "raw", out / "answer_key"
    for folder in (raw, key):
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)

    _write(business_rows(cal, businesses), raw / "businesses.parquet")
    _write(build_owners(cfg, businesses), raw / "owners.parquet")
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
    _write({
        "case_id": [k["case_id"] for k in cases], "business_id": [k["business_id"] for k in cases],
        "typology": [k["typology"] for k in cases], "variant": [k["variant"] for k in cases],
        "account_is_fraudulent": [k["account_is_fraudulent"] for k in cases],
        "case_start": _ts(cal, np.array([k["case_start_t"] for k in cases])),
        "case_end": _ts(cal, np.array([k["case_end_t"] for k in cases])),
        "loss_if_uncaught": [round(k["loss_if_uncaught"], 2) for k in cases],
    }, key / "fraud_cases.parquet")
    _write([{"business_id": b.business_id, "archetype": b.archetype} for b in businesses], key / "business_profile.parquet")
    return {"businesses": len(businesses), "transactions": n, "cases": len(cases), "payees": len(pay)}


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
