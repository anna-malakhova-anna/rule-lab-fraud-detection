# DRAFT: Rule-change memo (Phase 1)

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Everything below is synthetic data. Bracketed notes are prompts, not text to keep.

## Recommendation

[One or two sentences: what I recommend changing, and the single number that justifies it.]

## Impact

### Fraud dollars, good customers, reviews per day (test months, held out)

<!-- memo-headline:start -->
| Measure (test months) | Champion (today) | Challenger (proposed) |
|---|---|---|
| Fraud $ prevented (90% range) | $985K ($475K to $1.58M) | $960K ($457K to $1.55M) |
| Share of fraud $ prevented | 82% (63% to 95%) | 80% (61% to 93%) |
| Fraud cases detected | 20 of 27 | 19 of 27 |
| Alerts that were fraud (precision) | 0.9% | 0.9% |
| Good businesses flagged | 2,302 | 2,359 |
| Good businesses with money held | 1,788 | 2,010 |
| Payrolls delayed | 999 | 999 |
| Good-customer dollar-days held | $141.73M | $204.28M |
| Reviews per business day (avg / max) | 52.3 / 126 | 53.6 / 125 |
| Days over review capacity | 33 of 129 | 33 of 129 |
<!-- memo-headline:end -->

### What changes rule by rule

<!-- memo-thresholds:start -->
| Rule | Action | Champion cutoff | Challenger cutoff |
|---|---|---|---|
| R1 Check money out fast | hold | >= 0.6 | >= 0.6 |
| R2 Check far above own baseline | hold | >= 1 | >= 0.5 |
| R3 Many new check payers | rfi | >= 4 | >= 5 |
| R4 First payment to changed bank details | hold | <= 14 | <= 7 |
| R5 Payment far above usual for payee | rfi | >= 3 | >= 4 |
<!-- memo-thresholds:end -->

<!-- memo-rules:start -->
| Rule alone, champion cutoff (test months) | Cases detected | Fraud $ prevented | Good businesses flagged | Payrolls delayed | Reviews/day |
|---|---|---|---|---|---|
| R1 Check money out fast | 9 of 27 | $428K | 1,403 | 999 | 20.1 |
| R2 Check far above own baseline | 7 of 27 | $287K | 288 | 0 | 3.2 |
| R3 Many new check payers | 5 of 27 | $69K | 247 | 0 | 7.5 |
| R4 First payment to changed bank details | 11 of 27 | $486K | 287 | 0 | 2.4 |
| R5 Payment far above usual for payee | 12 of 27 | $259K | 756 | 0 | 21.3 |
<!-- memo-rules:end -->

## Risks

[What could make this wrong: small test sample, synthetic typologies, cost assumptions, fraud adapting.]

### Payroll

<!-- memo-payroll:start -->
| Rule | Period | Good payrolls held |
|---|---|---|
| R1 Check money out fast | test | 999 |
| R1 Check money out fast | train | 1512 |

Review capacity: 60 reviews per business day. Champion test-period days over capacity: 33 of 129.
<!-- memo-payroll:end -->

### Overlap between rules

<!-- memo-overlap:start -->
| Rule (champion set, test months) | Cases it touched | Cases ONLY it touched |
|---|---|---|
| R1 Check money out fast | 9 | 0 |
| R2 Check far above own baseline | 7 | 0 |
| R3 Many new check payers | 5 | 0 |
| R4 First payment to changed bank details | 11 | 4 |
| R5 Payment far above usual for payee | 12 | 0 |
<!-- memo-overlap:end -->

## What to monitor after the change

[Alert volume per rule per week; precision once outcomes mature; payrolls held; days over review capacity;
returned checks and losses that no rule touched.]
