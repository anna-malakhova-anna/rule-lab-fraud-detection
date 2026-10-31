"""Regenerate the numbers blocks in README.md and the memo draft from the warehouse.

  uv run python -m scripts.render_results           # rewrite the blocks
  uv run python -m scripts.render_results --check   # exit 1 if a block is out of date (used by the tests)

Only the text between the markers is generated; everything else in those files is hand-written.
"""
from __future__ import annotations

import re
import sys

from scripts import results as R
from scripts.common import ROOT

README = ROOT / "README.md"
MEMO = ROOT / "docs" / "memo" / "rule-change-memo-phase2-DRAFT.md"
INVESTIGATION = ROOT / "docs" / "investigations" / "INV-001-ach-debit-returns.md"


def readme_block() -> str:
    w, t = R.window(), R.totals()
    table = R.markdown_table(["Test months (held out)", "Champion", "Challenger"], R.headline_rows())
    return (f"Synthetic data: {t['businesses']:,} businesses, {t['transactions']:,} transactions, {t['cases']} planted fraud cases "
            f"({t['test_cases']} start in the held-out test months, {w['train_end']:%b %Y} onward). "
            f"Ranges are 90% bootstrap ranges over businesses.\n\n{table}")


def memo_blocks() -> dict[str, str]:
    m_test = R.strategy_metrics("test")
    headline = R.markdown_table(["Measure (test months)", "Champion (today)", "Challenger (proposed)"], R.headline_rows())

    rules = R.challenger_thresholds()
    thresholds = R.markdown_table(
        ["Rule", "Action", "Champion", "Challenger"],
        [(R.RULE_LABELS[r["rule_id"]], r["action"], R.champion_cell(r), R.challenger_cell(r)) for r in rules])

    # Each rule alone, at the cutoff the challenger runs it at, on the test months.
    sweep_test = {(r["rule_id"], r["cutoff"]): r for r in R.sweep("test")}
    per_rule = []
    for r in rules:
        m = sweep_test[(r["rule_id"], r["challenger_cutoff"])]
        per_rule.append((R.RULE_LABELS[r["rule_id"]], f"{m['cases_detected']} of {m['cases']}", R.usd(m["loss_prevented"]),
                         R.num(m["good_businesses_flagged"]), R.num(m["good_applicants_declined"]), R.num(m["reviews_per_day"], 1)))
    rules_table = R.markdown_table(
        ["Rule alone, challenger cutoff (test months)", "Cases touched", "Fraud $ prevented", "Good businesses flagged",
         "Good applicants declined", "Reviews/day"], per_rule)

    champ = R.typology_totals("champion")
    chall = R.typology_totals("challenger")
    typ_rows = []
    for t, label in R.TYPOLOGY_LABELS.items():
        a, b = champ.get(t), chall.get(t)
        if a:
            typ_rows.append((label, a["cases"], a["detected"], b["detected"], R.usd(a["loss"]), R.usd(a["prevented"]), R.usd(b["prevented"])))
    typology_table = R.markdown_table(
        ["Fraud type (test months)", "Cases", "Detected: champion", "Detected: challenger", "Loss at stake",
         "Prevented: champion", "Prevented: challenger"], typ_rows)

    overlap = [(R.RULE_LABELS[o["rule_id"]], o["cases_detected"], o["cases_only_this_rule"])
               for o in R.overlap("challenger") if o["period"] == "test"]
    overlap_table = R.markdown_table(["Rule (challenger set, test months)", "Cases it touched", "Cases ONLY it touched"], overlap)

    gap = [(R.RULE_LABELS[g["rule_id"]], f"{g['challenger_cutoff']:g}", f"{g['cases_known']} of {g['cases_all']}",
            R.usd(g["prevented_known"]), R.usd(g["prevented_all"]), R.pct(g["precision_known"], 1), R.pct(g["precision_all"], 1))
           for g in R.label_delay_gap()]
    gap_table = R.markdown_table(
        ["Tuned rule (training months)", "Cutoff", "Cases the bank knew of", "Prevented, as seen then", "Prevented, all labels",
         "Precision, as seen then", "Precision, all labels"], gap)

    cap = m_test["champion"]
    return {
        "memo-headline": headline,
        "memo-thresholds": thresholds,
        "memo-rules": rules_table,
        "memo-typology": typology_table,
        "memo-overlap": overlap_table,
        "memo-label-delay": gap_table,
        "memo-capacity": f"Review capacity: {R.window()['reviews_capacity_per_day']:g} reviews per business day. "
                         f"Days over capacity in the test months: champion {cap['days_over_capacity']}, "
                         f"challenger {m_test['challenger']['days_over_capacity']}, of {cap['business_days']}.",
        "inv-facts": investigation_facts(),
    }


def investigation_facts() -> str:
    eff = {e["rule_id"]: e for e in R.effective_dates()}["R9_ach_pull_then_fast_out"]
    weeks = R.weekly_return_series("ach_debit_in:unauthorized")
    before = [w for w in weeks if w["week"] < eff["detected_at"].date()]
    first = next(w for w in weeks if w["is_alarm"])
    after = [w for w in weeks if w["week"] >= eff["detected_at"].date()]
    ach = R.typology_totals("champion")["ach_return_fraud"]
    ach_c = R.typology_totals("challenger")["ach_return_fraud"]
    rows = [
        ("Unauthorized ACH-debit returns, all weeks before the alarm", f"{sum(w['returns'] for w in before)}"),
        ("First alarm (week of)", f"{first['week']:%d %b %Y}: {first['returns']} returns vs a trailing mean of {first['baseline_mean']:.1f}"),
        ("Alarm visible (week closes)", f"{eff['detected_at']:%d %b %Y}"),
        ("Answering rule (R9) live from", f"{eff['effective_from']:%d %b %Y}"),
        ("Unauthorized ACH-debit returns after the alarm", f"{sum(w['returns'] for w in after)} ({R.usd(sum(w['returned_amount'] for w in after))})"),
        ("Share of those returned dollars no champion rule had alerted on",
         R.pct(sum(w["unalerted_amount"] for w in after) / max(1, sum(w["returned_amount"] for w in after)))),
        ("ACH return fraud cases starting in the test months", f"{ach['cases']}"),
        ("Prevented by the champion (no ACH rule)", f"{R.usd(ach['prevented'])} of {R.usd(ach['loss'])}"),
        ("Prevented by the challenger (with R9 from its live date)", f"{R.usd(ach_c['prevented'])} of {R.usd(ach_c['loss'])}"),
    ]
    return R.markdown_table(["Fact (from the warehouse)", "Value"], rows)


def num_or(x) -> str:
    return R.num(x)


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"marker <!-- {name}:start --> not found")
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)


def render() -> dict:
    out = {README: replace_block(README.read_text(), "results", readme_block())}
    blocks = memo_blocks()
    for path in (MEMO, INVESTIGATION):
        text = path.read_text()
        for name, body in blocks.items():
            if f"<!-- {name}:start -->" in text:
                text = replace_block(text, name, body)
        out[path] = text
    return out


def main() -> int:
    rendered = render()
    stale = [p for p, text in rendered.items() if p.read_text() != text]
    if "--check" in sys.argv:
        for p in stale:
            print(f"{p.relative_to(ROOT)} is out of date with the warehouse: run `make results`", file=sys.stderr)
        return 1 if stale else 0
    for p, text in rendered.items():
        p.write_text(text)
    print(f"updated {len(stale)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
