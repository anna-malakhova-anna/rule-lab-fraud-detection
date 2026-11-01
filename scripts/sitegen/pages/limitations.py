"""The limitations page."""
from __future__ import annotations

from scripts import results as R
from scripts.sitegen.components import page_title


def limitations() -> str:
    t = R.totals()
    return f"""{page_title("How sure are we?", "What flatters these numbers, and what they leave out")}
<h2>What flatters these results</h2>
<ul>
<li><strong>I wrote the fraud.</strong> The rules look for exactly the shapes I planted, so detection rates in the 90s say more about my generator than about any real bank. Real fraud adapts once it starts getting caught.</li>
<li><strong>Synthetic bust-outs are clean.</strong> Every one draws the full line within days of an increase, which R12 catches almost perfectly. Real bust-outs are messier and slower.</li>
<li><strong>The final grade uses the full answer key.</strong> Tuning only sees labels known by month 12, but the headline comparison uses every label, including cases a real bank would never confirm.</li>
<li><strong>Generator shortcuts can leak into results.</strong> I've found and fixed two. Bust-out money sent back to the owner's own account made R5 look like a bust-out detector. ACH fraud cash-outs to the owner's account let R5 catch part of the month-12 pattern by luck. I documented the second rather than removing it.</li>
</ul>
<h2>What makes them uncertain</h2>
<ul>
<li><strong>Small samples.</strong> The test months hold {t["test_cases"]} cases across seven fraud types, 6 to 22 each. One case moves a fraud type's numbers a lot; the headline carries bootstrap ranges for that reason.</li>
<li><strong>Invented costs.</strong> Cutoffs are chosen with costs I made up (config/backtest.yaml): $30 a review, $150 per good business flagged, $1,000 per delayed payroll, $300 per good applicant declined. Different costs pick different cutoffs.</li>
<li><strong>Vendors that know the answer.</strong> The invented vendors' scores are drawn from the planted truth with noise. A real vendor's signal is murkier, and whether it adds anything depends on how much the in-house rules already cover.</li>
<li><strong>Fraudsters adapt once.</strong> After the instant-payout launch, fraudsters switch to instant and split cash-outs under the cap, but they don't yet adapt to the launch controls themselves.</li>
<li><strong>A simple queue.</strong> The Risk Ops simulation assumes the same capacity every day, one decision per case, no escalation tier, and invented analyst error rates (10% of fraud cleared by mistake, 2% of good cases flagged).</li>
<li><strong>Simplified mechanics.</strong> There are no account balances or overdrafts, an RFI is assumed to stop half the fraud, and a hold is assumed to stop all of it.</li>
<li><strong>A thin tuning set for credit.</strong> Bust-out labels arrive about five months after the money leaves, so tuning in month 12 saw only a handful of confirmed bust-outs.</li>
</ul>
<h2>What isn't modelled</h2>
<ul>
<li>Fraud that adapts to the rules: a ring buying aged shelf companies to dodge R6's decline, or money moved out through fake payroll runs to dodge R1.</li>
<li>Customer reactions to friction (churn), chargebacks, and the card rail beyond aggregate spend.</li>
</ul>
"""
