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
MEMO = ROOT / "docs" / "memo" / "rule-change-memo-phase3-DRAFT.md"


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
        [(R.RULE_LABELS[r["rule_id"]], R.action_cell(r), R.champion_cell(r), R.challenger_cell(r)) for r in rules])

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
        "memo-credit-loss": credit_loss_table(),
    }


def credit_loss_table() -> str:
    """Honest defaults: a separate line, never added to fraud prevented (ADR-016)."""
    cl = R.credit_losses()
    rows = []
    for period in ("test", "train"):
        ch, cc = cl.get(("champion", period)), cl.get(("challenger", period))
        if not ch:
            continue
        rows += [
            (f"Honest businesses that defaulted ({period} months)", ch["honest_defaults"], cc["honest_defaults"]),
            (f"Balance when they missed a payment ({period})", R.usd(ch["balance_at_missed_payment"]), R.usd(cc["balance_at_missed_payment"])),
            (f"Of which flagged by a rule in the 90 days before ({period})", R.usd(ch["balance_flagged_before_default"]),
             R.usd(cc["balance_flagged_before_default"])),
            (f"Holds put on these struggling businesses ({period})", ch["holds_on_honest_defaulters"], cc["holds_on_honest_defaulters"]),
        ]
    return R.markdown_table(["Credit losses that are NOT fraud", "Champion", "Challenger"], rows)


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
    for path in (MEMO,):
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
