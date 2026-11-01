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
| Fraud $ prevented (90% range) | $3.33M ($2.39M to $4.35M) | $3.89M ($2.90M to $4.95M) |
| Share of fraud $ prevented | 69% (60% to 76%) | 80% (74% to 86%) |
| Fraud cases detected | 68 of 80 | 79 of 80 |
| Alerts that were fraud (precision) | 2.6% | 2.9% |
| Good businesses flagged | 3,673 | 3,831 |
| Good businesses with money held | 3,044 | 3,203 |
| Good applicants declined | 1 | 1 |
| Payrolls delayed | 0 | 0 |
| Good-customer dollar-days held | $280.12M | $285.49M |
| Reviews per business day (avg / max) | 85.7 / 181 | 88.4 / 186 |
| Days over review capacity | 48 of 129 | 53 of 129 |
<!-- memo-headline:end -->

### By fraud type

<!-- memo-typology:start -->
| Fraud type (test months) | Cases | Detected: champion | Detected: challenger | Loss at stake | Prevented: champion | Prevented: challenger |
|---|---|---|---|---|---|---|
| Check deposit fraud | 10 | 10 | 10 | $991K | $918K | $918K |
| Vendor bank-detail change (BEC) | 6 | 5 | 5 | $81K | $74K | $74K |
| Synthetic / shell businesses | 9 | 9 | 9 | $581K | $581K | $581K |
| Money mules | 10 | 10 | 10 | $631K | $599K | $599K |
| Account takeover | 8 | 8 | 8 | $253K | $160K | $160K |
| ACH return fraud (emerging, month 12) | 22 | 22 | 22 | $1.33M | $683K | $683K |
| Credit bust-out | 15 | 4 | 15 | $970K | $318K | $875K |
<!-- memo-typology:end -->

### Credit losses that are not fraud

<!-- memo-credit-loss:start -->
| Credit losses that are NOT fraud | Champion | Challenger |
|---|---|---|
| Honest businesses that defaulted (test months) | 77 | 77 |
| Balance when they missed a payment (test) | $2.03M | $2.03M |
| Of which flagged by a rule in the 90 days before (test) | $558K | $726K |
| Holds put on these struggling businesses (test) | 185 | 200 |
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
| R1 Check money out fast | 29 of 80 | $1.89M | 2,119 | 0 | 29.0 |
| R2 Check far above own baseline | 17 of 80 | $1.04M | 1,063 | 0 | 16.4 |
| R3 Many new check payers | 9 of 80 | $272K | 203 | 0 | 6.8 |
| R4 First payment to changed bank details | 5 of 80 | $74K | 213 | 0 | 1.7 |
| R5 Payment far above usual for payee | 12 of 80 | $196K | 957 | 0 | 28.1 |
| R6 Applicant shares identity with others | 17 of 80 | $801K | 177 | 1 | 1.5 |
| R7 Many new senders, swept out | 10 of 80 | $593K | 69 | 0 | 3.8 |
| R8 New device, contact change, new payee | 8 of 80 | $160K | 0 | 0 | 0.1 |
| R9 ACH debit money out fast | 23 of 80 | $557K | 293 | 0 | 4.5 |
| R10 Inflows ramped before a credit decision | 9 of 80 | $291K | 38 | 0 | 0.4 |
| R11 Credit draw money out fast | 14 of 80 | $332K | 241 | 0 | 2.5 |
| R12 Line drawn to limit soon after increase | 15 of 80 | $792K | 0 | 0 | 0.1 |
<!-- memo-rules:end -->

## Risks

[Bust-out labels arrive about five months late, so tuning saw few cases; synthetic bust-outs are cleaner than
real ones; seasonal businesses asking for increases in spring; review capacity.]

### Review capacity

<!-- memo-capacity:start -->
Review capacity: 90 reviews per business day. Days over capacity in the test months: champion 48, challenger 53, of 129.
<!-- memo-capacity:end -->

### Tuning on the labels we actually had

<!-- memo-label-delay:start -->
| Tuned rule (training months) | Cutoff | Cases the bank knew of | Prevented, as seen then | Prevented, all labels | Precision, as seen then | Precision, all labels |
|---|---|---|---|---|---|---|
| R10 Inflows ramped before a credit decision | 3 | 120 of 154 | $380K | $753K | 13.5% | 28.4% |
| R11 Credit draw money out fast | 0.3 | 120 of 154 | $507K | $1.24M | 4.4% | 9.8% |
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
