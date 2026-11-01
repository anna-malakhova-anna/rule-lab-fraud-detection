"""The case summaries demo page (module G)."""
from __future__ import annotations

from scripts import results as R
from scripts.case_summaries import CITATIONS
from scripts.sitegen.components import catbar, esc, page_title, table


def _summary_html(text: str) -> str:
    out = []
    for line in text.splitlines():
        m = CITATIONS.search(line)
        claim, cites = (line[:m.start()], m.group(1)) if m else (line, "")
        out.append(f'<p class="summary">{esc(claim)}<span class="cite">{esc(cites)}</span></p>')
    return "".join(out)


def summaries() -> str:
    t = R.summary_totals()
    checks = R.summary_checks()
    designed = [c for c in checks if c["designed_to_catch"]]
    caught = sum(c["caught"] for c in designed) / sum(c["summaries"] for c in designed)
    rows = [[c["corruption"], "yes" if c["designed_to_catch"] else "no: a known limit", c["summaries"], c["caught"],
             R.pct(c["catch_rate"], 1)] for c in checks]
    cards = "".join(
        f'<div class="card"><h3>{esc(R.RULE_LABELS[e["alerts"][0]["rule_id"]])}</h3>{_summary_html(e["summary"])}'
        f'<p class="src">Case {esc(e["case_id"])}</p></div>' for e in R.summary_examples())
    return f"""{page_title("Case summaries", "Two or three lines per case, every claim traced to the case")}
{catbar([("#examples", "Examples"), ("#guardrail", "The guardrail"), ("#limits", "What it can't catch")])}
<p>When a case opens, the analyst gets a short summary: who the business is, what it is queued for, and the evidence
behind its strongest alerts. Every line ends with the case fields it rests on (shown in grey). A check rejects any line
that cites nothing, cites a field the case doesn't have, names the wrong rule, or states a number or date its fields
don't hold. Summaries here come from a fixed template: no language model and no API key, so the project builds
offline. A model can be swapped in later behind the same check.</p>
<div class="stats">
<div class="stat"><b>{t["summaries"]:,}</b><span>cases summarised; {t["failing"]:,} fail the check</span></div>
<div class="stat"><b>{R.pct(caught, 1)}</b><span>of deliberately corrupted summaries rejected, for the five kinds of error the check is built to catch</span></div>
</div>

<h2 id="examples">Examples</h2>
<p>The first case in the window whose strongest alert comes from each rule.</p>
<div class="grid">{cards}</div>

<h2 id="guardrail">The guardrail, measured</h2>
<p>Template summaries can't invent anything, so their error rate is zero by construction. To show what the check
itself catches, the summaries of a sample of cases were corrupted in known ways.</p>
<div class="card">{table(["Corruption", "Should the check reject it?", "Summaries", "Rejected", "Rejection rate"], rows, {2, 3, 4})}</div>
<p class="src">Source: analysis.summary_checks (scripts/case_summaries.py). Write-up: docs/summaries/case-summaries-DRAFT.md</p>

<h2 id="limits">What it can't catch</h2>
<p>The check proves that what a line says can be traced to the case, not that it means what the case means. A made-up
sentence with no numbers that cites a real field passes, and two cited numbers swapped into each other's places still
match. Before release, the check did catch template lines describing applicants as "open -4 days", and it surfaced a
data bug: some accounts had activity before they opened. Both were fixed.</p>
"""
