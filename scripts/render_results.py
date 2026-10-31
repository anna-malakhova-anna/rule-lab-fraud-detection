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
MEMO = ROOT / "docs" / "memo" / "rule-change-memo-DRAFT.md"


def readme_block() -> str:
    w, t = R.window(), R.totals()
    table = R.markdown_table(["Test months (held out)", "Champion", "Challenger"], R.headline_rows())
    return (f"Synthetic data: {t['businesses']:,} businesses, {t['transactions']:,} transactions, {t['cases']} planted fraud cases "
            f"({t['test_cases']} start in the held-out test months, {w['train_end']:%b %Y} onward). "
            f"Ranges are 90% bootstrap ranges over businesses.\n\n{table}")


def memo_blocks() -> dict[str, str]:
    m_test = R.strategy_metrics("test")
    headline = R.markdown_table(["Measure (test months)", "Champion (today)", "Challenger (proposed)"], R.headline_rows())

    thresholds = R.markdown_table(
        ["Rule", "Action", "Champion cutoff", "Challenger cutoff"],
        [(R.RULE_LABELS[r["rule_id"]], r["action"], f"{r['comparator']} {r['champion_cutoff']:g}",
          R.challenger_cell(r)) for r in R.challenger_thresholds()])

    sweep_test = {(r["rule_id"], r["cutoff"]): r for r in R.sweep("test") if r["scope"] == "as_written"}
    per_rule = []
    for r in R.challenger_thresholds():
        champ = sweep_test[(r["rule_id"], r["champion_cutoff"])]
        per_rule.append((R.RULE_LABELS[r["rule_id"]], f"{champ['cases_detected']} of {champ['cases']}", R.usd(champ["loss_prevented"]),
                         num_or(champ["good_businesses_flagged"]), num_or(champ["payrolls_delayed"]), R.num(champ["reviews_per_day"], 1)))
    rules_table = R.markdown_table(
        ["Rule alone, champion cutoff (test months)", "Cases detected", "Fraud $ prevented", "Good businesses flagged",
         "Payrolls delayed", "Reviews/day"], per_rule)

    overlap = [(R.RULE_LABELS[o["rule_id"]], o["cases_detected"], o["cases_only_this_rule"])
               for o in R.overlap("champion") if o["period"] == "test"]
    overlap_table = R.markdown_table(["Rule (champion set, test months)", "Cases it touched", "Cases ONLY it touched"], overlap)

    payroll = [(R.RULE_LABELS[p["rule_id"]], p["period"], p["payrolls_delayed"]) for p in R.payroll_by_rule("champion")]
    payroll_table = R.markdown_table(["Rule", "Period", "Good payrolls held"], payroll) if payroll else "_No payrolls delayed._"
    cap = m_test["champion"]
    return {
        "memo-headline": headline,
        "memo-thresholds": thresholds,
        "memo-rules": rules_table,
        "memo-overlap": overlap_table,
        "memo-payroll": payroll_table + f"\n\nReview capacity: {R.window()['reviews_capacity_per_day']:g} reviews per business day. "
                                        f"Champion test-period days over capacity: {cap['days_over_capacity']} of {cap['business_days']}.",
    }


def num_or(x) -> str:
    return R.num(x)


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"marker <!-- {name}:start --> not found")
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), text)


def render() -> dict:
    out = {README: replace_block(README.read_text(), "results", readme_block())}
    memo = MEMO.read_text()
    for name, body in memo_blocks().items():
        memo = replace_block(memo, name, body)
    out[MEMO] = memo
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
