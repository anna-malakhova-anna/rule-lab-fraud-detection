"""Case summaries cite their case, and the check rejects what it cannot trace (module G)."""
import datetime as dt

from scripts import case_summaries as S
from scripts.common import ROOT, load_yaml

ROW = {
    "action": "hold", "legal_name": "Route 66 Supply LLC", "industry": "retail", "open_date": dt.date(2022, 3, 1),
    "tenure_days": 1200, "stated_monthly_revenue": 40000.0,
    "alerts": [{"rule_id": "R1_check_then_fast_out", "reason_code": "CHK_OUT_FAST", "action": "hold", "txn_type": "wire_out",
                "amount": 20000.0, "score": 0.8,
                "evidence": '{"out_48h_incl_this": 33141.4, "normal_week_outflow": 26616.75, "checks_prior_72h": 13216.46}'}],
}
F = S.case_fields(ROW)


def test_template_summary_passes_and_cites_every_line():
    text = S.template_summary(F)
    assert S.check(text, F) == []
    lines = text.splitlines()
    assert 2 <= len(lines) <= 3 and all(S.CITATIONS.search(x) for x in lines)
    assert "$33,141" in text and "Route 66" in text      # digits inside a cited name are not claims


def test_check_rejects_untraceable_claims():
    good = S.line("R1: $33,141 went out", "alerts[0].rule_id", "alerts[0].evidence.out_48h_incl_this")
    assert S.check(good, F) == []
    bad = {
        "uncited": "R1: $33,141 went out",
        "wrong number": S.line("R1: $34,141 went out", "alerts[0].rule_id", "alerts[0].evidence.out_48h_incl_this"),
        "too precise": S.line("R1: $33,141.47 went out", "alerts[0].rule_id", "alerts[0].evidence.out_48h_incl_this"),
        "missing field": S.line("R1: $33,141 went out", "alerts[0].rule_id", "alerts[0].evidence.prior_fraud_reports"),
        "wrong rule": S.line("R7: $33,141 went out", "alerts[0].rule_id", "alerts[0].evidence.out_48h_incl_this"),
        "uncited number": S.line("R1: $33,141 went out to 3 new payees", "alerts[0].rule_id", "alerts[0].evidence.out_48h_incl_this"),
        "wrong date": S.line("Opened 2022-03-02", "business.open_date"),
        "wrong sign": S.line("Open -1200 days", "business.tenure_days"),
        # One cited value can't back two numbers: 0.8 rounds to 1, but it already backs the 0.8.
        "value used twice": S.line("R1: score 0.8, from 1 deposit", "alerts[0].rule_id", "alerts[0].score"),
    }
    for name, text in bad.items():
        assert S.check(text, F), name


def test_check_cannot_judge_meaning():
    """The documented limit: a cited sentence with no numbers passes whatever it says."""
    assert S.check(S.line("The owner was reported for fraud elsewhere", "business.industry"), F) == []


def test_summaries_are_offline_and_deterministic():
    assert set(S.WRITERS) == {"template"} and load_yaml("case_summaries.yaml")["writer"] in S.WRITERS
    source = (ROOT / "scripts" / "case_summaries.py").read_text()
    for lib in ("anthropic", "openai", "requests", "httpx", "urllib"):
        assert f"import {lib}" not in source
    assert S.template_summary(F) == S.template_summary(S.case_fields(ROW))


def test_every_stored_summary_passes_its_check(con):
    failing, total = con.execute("select count(*) filter (where problems > 0), count(*) from analysis.case_summaries").fetchone()
    assert total > 0 and failing == 0
    cases = con.execute("select count(*) from cases.case_records").fetchone()[0]
    assert cases == total


def test_every_queued_rule_has_its_own_template(con):
    """Each rule that reaches the queue gets a specific line, not the generic score fallback."""
    cur = con.execute("""
        select * from cases.case_records
        qualify row_number() over (partition by alerts[1].rule_id order by case_id) = 1""")
    cols = [d[0] for d in cur.description]
    for r in cur.fetchall():
        row = dict(zip(cols, r))
        f = S.case_fields(row)
        assert S._alert_line(f, 0) is not None, row["alerts"][0]["rule_id"]


def test_guardrail_catches_what_it_is_built_to_catch(con):
    rows = con.execute("select corruption, designed_to_catch, summaries, catch_rate from analysis.summary_checks").fetchall()
    assert len(rows) == len(S.CORRUPTIONS)
    for name, designed, n, rate in rows:
        assert n > 0, name
        if designed:
            assert rate == 1.0, name


def test_case_records_carry_no_truth(con):
    cols = {r[0] for r in con.execute("describe cases.case_records").fetchall()}
    assert not cols & {"is_fraud", "label", "typology", "fraud_case_id", "loss_amount"}
