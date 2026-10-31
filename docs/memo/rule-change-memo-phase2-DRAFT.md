# DRAFT: Rule-change memo (Phase 2)

> **DRAFT. Numbers are FROZEN from the Phase 2 build (commit 4b76799: 12,000 businesses, six typologies).**
> Check out that commit and run `make all` to reproduce them. The prose is mine to write.
> Everything below is synthetic data. Bracketed notes are prompts, not text to keep.
> Champion = the Phase 1 challenger, promoted (ADR-010). Challenger = champion + R6, R7, R8, and R9 from the
> day it went live after the ACH-return alarm (ADR-014).

## Recommendation

[One or two sentences: which of R6-R9 to adopt, at what cutoffs, and the single number that justifies it.]

## Impact

### Fraud dollars, good customers, reviews per day (test months, held out)

| Measure (test months) | Champion (today) | Challenger (proposed) |
|---|---|---|
| Fraud $ prevented (90% range) | $2.30M ($1.45M to $3.26M) | $3.96M ($2.94M to $5.14M) |
| Share of fraud $ prevented | 55% (43% to 66%) | 95% (92% to 97%) |
| Fraud cases detected | 42 of 71 | 66 of 71 |
| Alerts that were fraud (precision) | 1.5% | 3.5% |
| Good businesses flagged | 3,487 | 3,740 |
| Good businesses with money held | 2,965 | 3,122 |
| Good applicants declined | 0 | 0 |
| Payrolls delayed | 0 | 0 |
| Good-customer dollar-days held | $269.91M | $289.11M |
| Reviews per business day (avg / max) | 79.2 / 171 | 88.2 / 187 |
| Days over review capacity | 34 of 129 | 51 of 129 |

### By fraud type

| Fraud type (test months) | Cases | Detected: champion | Detected: challenger | Loss at stake | Prevented: champion | Prevented: challenger |
|---|---|---|---|---|---|---|
| Check deposit fraud | 13 | 13 | 13 | $1.05M | $1.05M | $1.05M |
| Vendor bank-detail change (BEC) | 10 | 6 | 6 | $182K | $154K | $154K |
| Synthetic / shell businesses | 5 | 5 | 5 | $385K | $385K | $385K |
| Money mules | 16 | 5 | 16 | $1.08M | $158K | $1.05M |
| Account takeover | 8 | 0 | 8 | $252K | $0 | $252K |
| ACH return fraud (emerging, month 12) | 19 | 13 | 18 | $1.20M | $543K | $1.06M |

### What changes rule by rule

| Rule | Action | Champion | Challenger |
|---|---|---|---|
| R1 Check money out fast | hold | >= 0.4 | >= 0.4 |
| R2 Check far above own baseline | hold | >= 0.5 | >= 0.5 |
| R3 Many new check payers | rfi | >= 5 | >= 5 |
| R4 First payment to changed bank details | hold | <= 7 | <= 7 |
| R5 Payment far above usual for payee | rfi | >= 4 | >= 4 |
| R6 Applicant shares identity with others | rfi; block at >= 3 | not running | >= 1 (tuned) |
| R7 Many new senders, swept out | hold | not running | >= 5 (tuned) |
| R8 New device, contact change, new payee | hold | not running | <= 12 (tuned) |
| R9 ACH debit money out fast | hold | not running | >= 0.4, from 12 Jan 2026 |

| Rule alone, challenger cutoff (test months) | Cases touched | Fraud $ prevented | Good businesses flagged | Good applicants declined | Reviews/day |
|---|---|---|---|---|---|
| R1 Check money out fast | 23 of 71 | $1.70M | 2,193 | 0 | 30.2 |
| R2 Check far above own baseline | 17 of 71 | $1.10M | 1,112 | 0 | 17.4 |
| R3 Many new check payers | 12 of 71 | $245K | 205 | 0 | 6.8 |
| R4 First payment to changed bank details | 5 of 71 | $147K | 225 | 0 | 1.8 |
| R5 Payment far above usual for payee | 16 of 71 | $398K | 964 | 0 | 28.4 |
| R6 Applicant shares identity with others | 10 of 71 | $495K | 174 | 0 | 1.4 |
| R7 Many new senders, swept out | 17 of 71 | $1.12M | 70 | 0 | 4.5 |
| R8 New device, contact change, new payee | 8 of 71 | $252K | 0 | 0 | 0.1 |
| R9 ACH debit money out fast | 17 of 71 | $978K | 281 | 0 | 4.3 |

## Risks

[Small samples per fraud type; synthetic typologies; the decline cost assumption behind R6; review capacity.]

### Review capacity

Review capacity: 90 reviews per business day. Days over capacity in the test months: champion 34, challenger 51, of 129.

### Tuning on the labels we actually had

| Tuned rule (training months) | Cutoff | Cases the bank knew of | Prevented, as seen then | Prevented, all labels | Precision, as seen then | Precision, all labels |
|---|---|---|---|---|---|---|
| R6 Applicant shares identity with others | 1 | 116 of 151 | $1.89M | $2.92M | 6.3% | 10.7% |
| R7 Many new senders, swept out | 5 | 116 of 151 | $1.21M | $1.99M | 14.9% | 24.5% |
| R8 New device, contact change, new payee | 12 | 116 of 151 | $848K | $858K | 96.0% | 100.0% |

### Overlap between rules

| Rule (challenger set, test months) | Cases it touched | Cases ONLY it touched |
|---|---|---|
| R1 Check money out fast | 23 | 1 |
| R2 Check far above own baseline | 17 | 0 |
| R3 Many new check payers | 12 | 0 |
| R4 First payment to changed bank details | 5 | 5 |
| R5 Payment far above usual for payee | 16 | 2 |
| R6 Applicant shares identity with others | 10 | 0 |
| R7 Many new senders, swept out | 17 | 10 |
| R8 New device, contact change, new payee | 8 | 8 |
| R9 ACH debit money out fast | 16 | 3 |

## What to monitor after the change

[Declined applicants per week (R6); alerts per rule; precision at 30 days vs eventual; unauthorized ACH-debit
returns that no rule alerted on; payroll-funded losses (the risk R1's payroll exemption opened).]
