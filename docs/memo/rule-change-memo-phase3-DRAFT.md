# DRAFT: Rule-change memo (Phase 3: the line of credit)

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Everything below is synthetic data. Bracketed notes are prompts, not text to keep.
> Champion = the Phase 2 challenger, promoted (ADR-016). Challenger = champion + R10, R11, R12 (credit rules).

## Recommendation

[One or two sentences: which credit rules to adopt, at what cutoffs, and the single number that justifies it.]

## Impact

### Fraud dollars, good customers, reviews per day (test months, held out)

<!-- memo-headline:start -->
| Measure (test months) | Champion (today) | Challenger (proposed) |
|---|---|---|
| Fraud $ prevented (90% range) | $3.86M ($2.84M to $5.02M) | $4.47M ($3.40M to $5.67M) |
| Share of fraud $ prevented | 80% (72% to 87%) | 92% (88% to 96%) |
| Fraud cases detected | 68 of 80 | 79 of 80 |
| Alerts that were fraud (precision) | 2.4% | 2.7% |
| Good businesses flagged | 3,670 | 3,826 |
| Good businesses with money held | 3,039 | 3,195 |
| Good applicants declined | 1 | 1 |
| Payrolls delayed | 0 | 0 |
| Good-customer dollar-days held | $280.49M | $285.73M |
| Reviews per business day (avg / max) | 85.9 / 186 | 88.5 / 190 |
| Days over review capacity | 49 of 129 | 52 of 129 |
<!-- memo-headline:end -->

### By fraud type

<!-- memo-typology:start -->
| Fraud type (test months) | Cases | Detected: champion | Detected: challenger | Loss at stake | Prevented: champion | Prevented: challenger |
|---|---|---|---|---|---|---|
| Check deposit fraud | 10 | 10 | 10 | $991K | $991K | $991K |
| Vendor bank-detail change (BEC) | 6 | 5 | 5 | $81K | $80K | $80K |
| Synthetic / shell businesses | 9 | 9 | 9 | $581K | $581K | $581K |
| Money mules | 10 | 10 | 10 | $631K | $622K | $622K |
| Account takeover | 8 | 8 | 8 | $253K | $253K | $253K |
| ACH return fraud (emerging, month 12) | 22 | 22 | 22 | $1.33M | $1.02M | $1.02M |
| Credit bust-out | 15 | 4 | 15 | $970K | $321K | $930K |
<!-- memo-typology:end -->

### Credit losses that are not fraud

<!-- memo-credit-loss:start -->
| Credit losses that are NOT fraud | Champion | Challenger |
|---|---|---|
| Honest businesses that defaulted (test months) | 77 | 77 |
| Balance when they missed a payment (test) | $2.03M | $2.03M |
| Of which flagged by a rule in the 90 days before (test) | $557K | $725K |
| Holds put on these struggling businesses (test) | 185 | 199 |
| Honest businesses that defaulted (train months) | 69 | 69 |
| Balance when they missed a payment (train) | $1.70M | $1.70M |
| Of which flagged by a rule in the 90 days before (train) | $245K | $330K |
| Holds put on these struggling businesses (train) | 153 | 170 |
<!-- memo-credit-loss:end -->

### What changes rule by rule

<!-- memo-thresholds:start -->
| Rule | Action | Champion | Challenger |
|---|---|---|---|
| R1 Check money out fast | hold | >= 0.4 | >= 0.4 |
| R2 Check far above own baseline | hold | >= 0.5 | >= 0.5 |
| R3 Many new check payers | rfi | >= 5 | >= 5 |
| R4 First payment to changed bank details | hold | <= 7 | <= 7 |
| R5 Payment far above usual for payee | rfi | >= 4 | >= 4 |
| R6 Applicant shares identity with others | rfi; block at >= 3 | >= 1 | >= 1 |
| R7 Many new senders, swept out | hold | >= 5 | >= 5 |
| R8 New device, contact change, new payee | hold | <= 12 | <= 12 |
| R9 ACH debit money out fast | hold | >= 0.4 | >= 0.4 |
| R10 Inflows ramped before a credit decision | rfi | not running | >= 3 (tuned) |
| R11 Credit draw money out fast | hold | not running | >= 0.3 (tuned) |
| R12 Line drawn to limit soon after increase | hold | not running | <= 14 (tuned) |
<!-- memo-thresholds:end -->

<!-- memo-rules:start -->
| Rule alone, challenger cutoff (test months) | Cases touched | Fraud $ prevented | Good businesses flagged | Good applicants declined | Reviews/day |
|---|---|---|---|---|---|
| R1 Check money out fast | 29 of 80 | $2.08M | 2,132 | 0 | 29.2 |
| R2 Check far above own baseline | 17 of 80 | $1.04M | 1,064 | 0 | 16.5 |
| R3 Many new check payers | 9 of 80 | $272K | 203 | 0 | 6.8 |
| R4 First payment to changed bank details | 5 of 80 | $80K | 216 | 0 | 1.8 |
| R5 Payment far above usual for payee | 12 of 80 | $238K | 958 | 0 | 28.3 |
| R6 Applicant shares identity with others | 17 of 80 | $801K | 177 | 1 | 1.5 |
| R7 Many new senders, swept out | 10 of 80 | $622K | 69 | 0 | 3.7 |
| R8 New device, contact change, new payee | 8 of 80 | $253K | 0 | 0 | 0.1 |
| R9 ACH debit money out fast | 23 of 80 | $964K | 277 | 0 | 4.2 |
| R10 Inflows ramped before a credit decision | 9 of 80 | $291K | 37 | 0 | 0.4 |
| R11 Credit draw money out fast | 14 of 80 | $809K | 233 | 0 | 2.4 |
| R12 Line drawn to limit soon after increase | 15 of 80 | $792K | 0 | 0 | 0.1 |
<!-- memo-rules:end -->

## Risks

[Bust-out labels arrive about five months late, so tuning saw few cases; synthetic bust-outs are cleaner than
real ones; seasonal businesses asking for increases in spring; review capacity.]

### Review capacity

<!-- memo-capacity:start -->
Review capacity: 90 reviews per business day. Days over capacity in the test months: champion 49, challenger 52, of 129.
<!-- memo-capacity:end -->

### Tuning on the labels we actually had

<!-- memo-label-delay:start -->
| Tuned rule (training months) | Cutoff | Cases the bank knew of | Prevented, as seen then | Prevented, all labels | Precision, as seen then | Precision, all labels |
|---|---|---|---|---|---|---|
| R10 Inflows ramped before a credit decision | 3 | 120 of 154 | $380K | $753K | 13.5% | 28.4% |
| R11 Credit draw money out fast | 0.3 | 120 of 154 | $507K | $1.24M | 4.5% | 9.9% |
| R12 Line drawn to limit soon after increase | 14 | 120 of 154 | $527K | $1.25M | 42.9% | 100.0% |
<!-- memo-label-delay:end -->

### Overlap between rules

<!-- memo-overlap:start -->
| Rule (challenger set, test months) | Cases it touched | Cases ONLY it touched |
|---|---|---|
| R1 Check money out fast | 29 | 0 |
| R2 Check far above own baseline | 17 | 0 |
| R3 Many new check payers | 9 | 0 |
| R4 First payment to changed bank details | 5 | 1 |
| R5 Payment far above usual for payee | 12 | 0 |
| R6 Applicant shares identity with others | 17 | 0 |
| R7 Many new senders, swept out | 10 | 6 |
| R8 New device, contact change, new payee | 8 | 7 |
| R9 ACH debit money out fast | 23 | 10 |
| R10 Inflows ramped before a credit decision | 9 | 0 |
| R11 Credit draw money out fast | 14 | 0 |
| R12 Line drawn to limit soon after increase | 15 | 0 |
<!-- memo-overlap:end -->

## What to monitor after the change

[Limit-increase requests and how many get an RFI; draws held per week; missed payments and charge-offs that no
rule flagged; R10's alerts on seasonal businesses in spring.]
