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
    for a in ("seasonal_heavy", "many_small_checks", "lumpy_contractor", "annual_big_invoice", "vendor_details_churn",
              "many_small_transfers", "new_bookkeeper"):
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


def test_typologies_planted_in_both_periods(con):
    rows = con.execute("select typology, period, count(*) from backtest.bt_cases group by all").fetchall()
    seen = {(t, p) for t, p, n in rows if n >= 4}
    for t in ("check_deposit_fraud", "bec_vendor_change", "synthetic_shell", "money_mule", "account_takeover"):
        assert {(t, "train"), (t, "test")} <= seen, t


def test_emerging_pattern_starts_in_month_12(con):
    first, train_end = con.execute("""
        select min(case_start), (select train_end from config.cfg_window)
        from answer_key.fraud_cases where typology = 'ach_return_fraud'""").fetchone()
    assert first.date() >= (train_end.replace(month=train_end.month - 1) if train_end.month > 1 else train_end.replace(year=train_end.year - 1, month=12))


def test_application_ids_never_collide_with_transactions(con):
    overlap = con.execute("""
        select count(*) from raw.applications a join raw.transactions t on t.txn_id = a.application_id""").fetchone()[0]
    assert overlap == 0


def test_legitimate_identity_sharing_exists(con):
    shared_devices = con.execute("""
        select count(*) from (select device_id from raw.applications group by 1 having count(*) >= 5)""").fetchone()[0]
    assert shared_devices >= 10, "bookkeeper devices should link several legitimate applicants"


def test_some_cases_are_never_labelled(con):
    never = con.execute("select count(*) from answer_key.fraud_cases where label_known_at is null").fetchone()[0]
    assert never > 0
