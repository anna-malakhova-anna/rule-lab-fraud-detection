# DRAFT: Pre-launch risk review: instant payouts

> **DRAFT. Numbers are generated from the warehouse by `make results`; the prose is mine to write.**
> Synthetic data. Instant payouts are simulated from their launch date, with fraudsters adapting to them
> (ADR-021). Bracketed notes are prompts, not text to keep.

## For the executive

[The decision: launch instant payouts with which controls. One line on the trade: fraud dollars vs. customers slowed.]

### Controls, each on its own and together (after launch)

<!-- launch-controls:start -->
| After launch | Fraud $ stopped | Added to today's rules | Good payouts slowed | Good businesses slowed | Net value | Launch with it? |
|---|---|---|---|---|---|---|
| Today's rules, no controls | $1.90M |  |  |  |  |  |
| C1 No instant payouts from young accounts | $1.93M | $25K | 2,219 | 360 | −$29K | no |
| C2 Cooling-off for new or changed payees | $2.25M | $345K | 33 | 25 | $342K | yes |
| C3 Cooling-off after a contact change or new device | $2.00M | $93K | 263 | 205 | $63K | yes |
| C4 No instant payouts from money that can still come back | $2.14M | $232K | 10,537 | 2,613 | −$159K | no |
| All four together | $2.27M | $366K | 12,332 | 2,743 | −$45K |  |
<!-- launch-controls:end -->

## Threat model: what gets faster or bigger

<!-- launch-threat:start -->
| Fraud type (test months) | Stopped before launch | Cash-outs sent instant after launch | Stopped after launch, no controls |
|---|---|---|---|
| Check deposit fraud | 100% | 25 of 25 | 84% |
| Vendor bank-detail change (BEC) | 100% | 5 of 7 | 59% |
| Synthetic / shell businesses | 100% | 13 of 16 | 100% |
| Money mules | 98% | 40 of 45 | 91% |
| Account takeover | n/a | 17 of 18 | 63% |
| ACH return fraud (emerging, month 12) | 86% | 59 of 64 | 46% |
| Credit bust-out | 52% | 42 of 45 | 22% |
<!-- launch-threat:end -->

[Which fraud types move to instant, and the new attack surface: a cash-out finished before any alert exists.]

## Rule blind spots: which rules stop working

<!-- launch-blind-spots:start -->
| Running rule | Reason code | Fraud $ it stopped before 01 Mar 2026 only at the cash-out itself |
|---|---|---|
| R1 Check money out fast | `CHK_OUT_FAST` | $790K |
| R8 New device, contact change, new payee | `ATO_SEQUENCE` | $524K |
| R5 Payment far above usual for payee | `PAYEE_AMOUNT_OUTLIER` | $405K |
| R7 Many new senders, swept out | `MULE_FAN_IN` | $236K |
| R4 First payment to changed bank details | `PAYEE_DETAILS_CHANGED` | $141K |
| R9 ACH debit money out fast | `ACH_DEBIT_OUT_FAST` | $71K |
| R2 Check far above own baseline | `CHK_ABOVE_BASELINE` | $0 |
| R3 Many new check payers | `CHK_NEW_PAYERS` | $0 |
| R6 Applicant shares identity with others | `APP_SHARED_IDENTITY` | $0 |
<!-- launch-blind-spots:end -->

[These rules caught fraud only at the cash-out itself. On an instant payout that alert arrives after the money is gone.]

## For ops

[What changes in the queue: launch controls need no review, but customers will ask why a payout went standard.
Playbooks for C1-C4 are in docs/playbooks/.]

## For engineering

<!-- launch-eng:start -->
| Control | Pre-send check | Cutoff | Reason code | What must be logged |
|---|---|---|---|---|
| C1 No instant payouts from young accounts | days since the account opened | <= 90 | `INSTANT_NEW_ACCOUNT` | `days_since_open`, `amount` |
| C2 Cooling-off for new or changed payees | hours since the payee was added or its bank details last changed | <= 72 | `INSTANT_NEW_PAYEE` | `days_since_payee_created`, `days_since_bank_details_change`, `amount` |
| C3 Cooling-off after a contact change or new device | hours since the last contact change or new-device login | <= 72 | `INSTANT_AFTER_CONTACT_CHANGE` | `hours_since_contact_change`, `hours_since_new_device`, `amount` |
| C4 No instant payouts from money that can still come back | returnable money received in the last few days / the payout amount | >= 0.5 | `INSTANT_UNCLEARED_FUNDS` | `checks_prior_72h`, `ach_debits_prior_5d`, `line_draws_prior_72h`, `amount` |
<!-- launch-eng:end -->

[Each control runs before the payout is sent; it needs these fields at decision time, inside the payment's
latency budget. A tripped control sends the payout the standard way: no refusal, no review.]
