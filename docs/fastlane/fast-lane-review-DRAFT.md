# DRAFT: Good-customer fast lane

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Synthetic data. The fast lane is built on the recommended rules (the challenger) and changes nothing for today's
> rules (ADR-023). Bracketed notes are prompts, not text to keep.

## The question

[Which good customers do the rules hurt most, and can we take friction off them without letting fraud through?]

## Where the alerts are mostly false

A business is in the fast lane while it has been open at least a year and has had no returned item (a bounced
check, a returned ACH debit) in the last 180 days. Both are things the bank sees.

<!-- fast-lane-segments:start -->
| Segment (training months) | Rule | Alerts | Of which fraud | Precision | Good customers' holds |
|---|---|---|---|---|---|
| established, clean | all rules | 9,986 | 265 | 2.7% | 7,093 |
| everyone else | all rules | 12,172 | 624 | 5.1% | 5,419 |
| established, clean | R1 Check money out fast | 3,885 | 35 | 0.9% | 3,850 |
| everyone else | R1 Check money out fast | 3,067 | 105 | 3.4% | 2,962 |
| established, clean | R2 Check far above own baseline | 2,034 | 24 | 1.2% | 2,010 |
| everyone else | R2 Check far above own baseline | 1,104 | 117 | 10.6% | 987 |
| established, clean | R3 Many new check payers | 116 | 24 | 20.7% | 1 |
| everyone else | R3 Many new check payers | 4,820 | 66 | 1.4% | 1 |
| established, clean | R4 First payment to changed bank details | 277 | 10 | 3.6% | 267 |
| everyone else | R4 First payment to changed bank details | 110 | 5 | 4.5% | 105 |
| established, clean | R5 Payment far above usual for payee | 2,958 | 6 | 0.2% | 456 |
| everyone else | R5 Payment far above usual for payee | 1,205 | 11 | 0.9% | 187 |
| everyone else | R6 Applicant shares identity with others | 389 | 32 | 8.2% | 0 |
| established, clean | R7 Many new senders, swept out | 274 | 96 | 35.0% | 178 |
| everyone else | R7 Many new senders, swept out | 1,295 | 287 | 22.2% | 1,008 |
| established, clean | R8 New device, contact change, new payee | 11 | 11 | 100.0% | 0 |
| everyone else | R8 New device, contact change, new payee | 11 | 11 | 100.0% | 0 |
| established, clean | R9 ACH debit money out fast | 693 | 5 | 0.7% | 688 |
| everyone else | R9 ACH debit money out fast | 402 | 7 | 1.7% | 395 |
| established, clean | R10 Inflows ramped before a credit decision | 60 | 19 | 31.7% | 0 |
| everyone else | R10 Inflows ramped before a credit decision | 14 | 2 | 14.3% | 0 |
| established, clean | R11 Credit draw money out fast | 253 | 26 | 10.3% | 227 |
| everyone else | R11 Credit draw money out fast | 62 | 5 | 8.1% | 57 |
| established, clean | R12 Line drawn to limit soon after increase | 24 | 24 | 100.0% | 0 |
| everyone else | R12 Line drawn to limit soon after increase | 4 | 4 | 100.0% | 0 |
<!-- fast-lane-segments:end -->

By industry, all rules together. Shown for discovery only: a few fraud cases per industry is too thin to set
policy on.

<!-- fast-lane-industries:start -->
| Industry (training months) | Rule | Alerts | Of which fraud | Precision | Good customers' holds |
|---|---|---|---|---|---|
| construction | all rules | 5,904 | 136 | 2.3% | 5,039 |
| creative agency | all rules | 393 | 55 | 14.0% | 281 |
| ecommerce | all rules | 506 | 56 | 11.1% | 392 |
| education services | all rules | 773 | 82 | 10.6% | 435 |
| healthcare clinic | all rules | 2,512 | 54 | 2.1% | 1,128 |
| landscaping | all rules | 4,097 | 33 | 0.8% | 1,410 |
| professional services | all rules | 3,439 | 161 | 4.7% | 1,535 |
| restaurant | all rules | 725 | 106 | 14.6% | 439 |
| retail | all rules | 2,591 | 125 | 4.8% | 854 |
| trucking | all rules | 1,218 | 81 | 6.7% | 999 |
<!-- fast-lane-industries:end -->

## What the fast lane does

For a fast-lane business, R1, R2 and R9 (the rules aimed at a fraudster's own account) send a document request
instead of a hold, on amounts below a cap. Rules that protect a victim (R4, R5, R8) and the credit rules keep their
action. The cap is swept, not tuned: under the stated costs a hold is priced only by the money it ties up, so net
value cannot choose it. The column to judge is fraud let through per hold avoided.

### Test months

<!-- fast-lane-tradeoff-test:start -->
| Rule set (test months) | Good holds avoided | Customer-hours of waiting saved | Good businesses no longer held | Fraud $ let through | Fraud $ per hold avoided | Net value change |
|---|---|---|---|---|---|---|
| Fast lane, below $5,000 | 949 | 45,552 | 248 | $0 | $0 | $2K |
| Fast lane, below $10,000 | 1,634 | 78,432 | 491 | $0 | $0 | $7K |
| Fast lane, below $25,000 | 2,717 | 130,416 | 963 | $222K | $82 | −$197K |
| Fast lane, any amount | 4,047 | 194,256 | 1,548 | $455K | $112 | −$367K |
| Clear every alert on fast-lane businesses | 4,444 | 213,312 | 1,851 | $1.99M | $449 | −$1.40M |
<!-- fast-lane-tradeoff-test:end -->

### Training months (what we would have seen when choosing)

<!-- fast-lane-tradeoff-train:start -->
| Rule set (train months) | Good holds avoided | Customer-hours of waiting saved | Good businesses no longer held | Fraud $ let through | Fraud $ per hold avoided | Net value change |
|---|---|---|---|---|---|---|
| Fast lane, below $5,000 | 1,494 | 71,712 | 246 | $0 | $0 | $3K |
| Fast lane, below $10,000 | 2,588 | 124,224 | 551 | $0 | $0 | $11K |
| Fast lane, below $25,000 | 4,341 | 208,368 | 1,050 | $0 | $0 | $41K |
| Fast lane, any amount | 6,421 | 308,208 | 1,664 | $591K | $92 | −$454K |
| Clear every alert on fast-lane businesses | 7,093 | 340,464 | 2,043 | $3.65M | $515 | −$2.89M |
<!-- fast-lane-tradeoff-train:end -->

[The training months show no fraud let through at the $25,000 cap; the test months do. Say what that means for
choosing a cap, and which cap you recommend.]

### Which fraud gets through

<!-- fast-lane-typologies:start -->
| Rule set (test months) | Fraud type | Fraud $ let through |
|---|---|---|
| Fast lane, below $25,000 | ACH return fraud (emerging, month 12) | $85K |
| Fast lane, below $25,000 | Check deposit fraud | $138K |
| Fast lane, any amount | ACH return fraud (emerging, month 12) | $85K |
| Fast lane, any amount | Check deposit fraud | $361K |
| Fast lane, any amount | Credit bust-out | $10K |
| Clear every alert on fast-lane businesses | Account takeover | $160K |
| Clear every alert on fast-lane businesses | ACH return fraud (emerging, month 12) | $169K |
| Clear every alert on fast-lane businesses | Vendor bank-detail change (BEC) | $74K |
| Clear every alert on fast-lane businesses | Check deposit fraud | $721K |
| Clear every alert on fast-lane businesses | Credit bust-out | $734K |
| Clear every alert on fast-lane businesses | Money mules | $134K |
<!-- fast-lane-typologies:end -->

[Why clearing every alert on established customers is the wrong design: takeovers, payment redirection and
bust-outs all hit established accounts.]

## Onboarding: approval rate vs. fraud

What moving R6's decline bar does, on top of the recommended rules. The approval rate counts every application,
including those the bank's existing checks already decline.

<!-- onboarding-decline-bar:start -->
| R6 declines at score (test months) | Applications | Declined by R6 | Good applicants declined | Fraudulent applicants declined | Approval rate | Fraud $ let through vs today | Net value change vs today |
|---|---|---|---|---|---|---|---|
| 3 (today) | 1,263 | 10 | 1 | 9 | 82.7% | $0 | $0 |
| 4 | 1,263 | 9 | 1 | 8 | 82.7% | $0 | $0 |
| 5 | 1,263 | 7 | 0 | 7 | 82.9% | $0 | $300 |
| never | 1,263 | 0 | 0 | 0 | 83.5% | $8K | −$8K |
<!-- onboarding-decline-bar:end -->

[R6's decline tier moves the approval rate by under a point; the bank's existing checks dominate it. Say whether
the decline tier is worth keeping.]

## Caveats

- A known cap invites splitting payments under it, as fraudsters did with the instant-payout cap (ADR-021). A cap on
  two days' outflow rather than per payment would resist that. [Decide whether to test it.]
- The fast lane needs a year of history, so it never helps a new business.
