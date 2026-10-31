"""The synthetic world: reproducible, realistic in the ways that matter, and honest about prevalence."""
import hashlib

import pytest

from generator.common import load_config
from generator.main import generate


def _digest(folder):
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*.parquet")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def test_same_seed_same_world(tmp_path):
    cfg = load_config()
    cfg["population"]["n_businesses"] = 300
    generate(cfg, tmp_path / "a")
    generate(cfg, tmp_path / "b")
    assert _digest(tmp_path / "a") == _digest(tmp_path / "b")


def test_fraud_prevalence_is_realistic_and_low(con):
    n_biz = con.execute("select count(*) from raw.businesses").fetchone()[0]
    n_fraud = con.execute("select count(distinct business_id) from answer_key.fraud_cases").fetchone()[0]
    assert 0.005 <= n_fraud / n_biz <= 0.02


def test_odd_but_legitimate_businesses_exist(con):
    archetypes = {r[0]: r[1] for r in con.execute("select archetype, count(*) from answer_key.business_profile group by 1").fetchall()}
    for a in ("seasonal_heavy", "many_small_checks", "lumpy_contractor", "annual_big_invoice", "vendor_details_churn"):
        assert archetypes.get(a, 0) >= 50, a


def test_payroll_runs_every_two_weeks(con):
    gaps = con.execute("""
        select date_diff('day', lag(txn_time) over (partition by business_id order by txn_time), txn_time) as gap
        from raw.transactions where txn_type = 'payroll' qualify gap is not null""").fetchall()
    share_14 = sum(1 for (g,) in gaps if g == 14) / len(gaps)
    assert share_14 > 0.99


def test_raw_tables_carry_no_fraud_labels(con):
    cols = {r[0] for r in con.execute(
        "select column_name from information_schema.columns where table_schema = 'raw'").fetchall()}
    assert not cols & {"case_id", "role", "loss_amount", "is_fraud", "archetype", "typology"}


def test_both_typologies_planted_in_both_periods(con):
    rows = con.execute("select typology, period, count(*) from backtest.bt_cases group by all").fetchall()
    seen = {(t, p) for t, p, n in rows if n >= 5}
    for t in ("check_deposit_fraud", "bec_vendor_change"):
        assert {(t, "train"), (t, "test")} <= seen
