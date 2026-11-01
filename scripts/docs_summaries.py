"""The case-summaries write-up (module G): docs/summaries/case-summaries-DRAFT.md.
Numbers and examples are generated; prose is a draft."""
from __future__ import annotations

from pathlib import Path

from scripts import results as R
from scripts.common import ROOT

DOC = ROOT / "docs" / "summaries" / "case-summaries-DRAFT.md"


def checks_table() -> str:
    t = R.summary_totals()
    rows = [(f"Summaries as the `{t['writer']}` writer wrote them", "no (they should all pass)", R.num(t["summaries"]), R.num(t["failing"]),
             R.pct(t["failing"] / t["summaries"], 2))]
    rows += [(c["corruption"], "yes" if c["designed_to_catch"] else "no (a known limit)", c["summaries"], c["caught"],
              R.pct(c["catch_rate"], 1)) for c in R.summary_checks()]
    return R.markdown_table(["Summaries checked", "Should the check reject them?", "Summaries", "Rejected", "Rejection rate"], rows)


def examples() -> str:
    out = []
    for e in R.summary_examples():
        lines = "\n".join(f"> {line}  " for line in e["summary"].splitlines())
        out.append(f"**Case {e['case_id']}** (strongest alert: {R.RULE_LABELS[e['alerts'][0]['rule_id']]})\n\n{lines}")
    return "\n\n".join(out)


def blocks() -> dict[str, str]:
    return {"summary-checks": checks_table(), "summary-examples": examples()}


def documents() -> dict[Path, dict[str, str]]:
    return {DOC: blocks()}
