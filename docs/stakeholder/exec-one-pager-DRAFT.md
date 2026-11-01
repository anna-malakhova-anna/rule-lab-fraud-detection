# DRAFT: Executive one-pager: credit rules for the line of credit

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Synthetic data. Bracketed notes are prompts, not text to keep.

## The decision

[One sentence: approve adding these rules to the running rule set.]

<!-- exec-decision:start -->
| Proposed rule | Action | Fires when |
|---|---|---|
| R10 Inflows ramped before a credit decision | rfi | >= 3 (tuned) |
| R11 Credit draw money out fast | hold | >= 0.3 (tuned) |
| R12 Line drawn to limit soon after increase | hold | <= 14 (tuned) |
<!-- exec-decision:end -->

## What it buys and what it costs

<!-- exec-numbers:start -->
| Test months (6, held out) | Today | With the change | Difference |
|---|---|---|---|
| Fraud $ prevented | $3.33M | $3.89M | $558K ($279K to $871K) |
| Good businesses flagged | 3,673 | 3,831 | 158 |
| Good businesses with money held | 3,044 | 3,203 | 159 |
| Reviews per business day | 85.7 | 88.4 | 2.7 |
<!-- exec-numbers:end -->

## Risk of not acting

<!-- exec-risk:start -->
| Risk of not acting | Value |
|---|---|
| Bust-out losses today's rules let through (test months) | $652K of $970K |
| Of which the change would have stopped | $558K |
| The same, per month | $93K |
<!-- exec-risk:end -->

[One or two sentences on why now, and the main caveat: synthetic bust-outs are cleaner than real ones.]
