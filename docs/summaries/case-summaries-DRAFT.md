# DRAFT: Case summaries for analysts

> **DRAFT. Numbers and examples are generated from the warehouse by `make results`; the prose is mine to write.**
> Synthetic data. Summaries are written by a deterministic template (no language model, no API key) and checked
> line by line against the case they describe (ADR-025). Bracketed notes are prompts, not text to keep.

## What an analyst sees

Each case gets two or three lines: who the business is and what it is queued for, then its strongest one or two
alerts and the evidence behind them. Every line ends with the case fields it rests on.

<!-- summary-examples:start -->
**Case 4885-20250101** (strongest alert: R1 Check money out fast)

> Williams Partners LLC (trucking, open 1134 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R1: $22,263 went out in two days against a normal week of $10,775, right after $5,338 of check deposits [alerts[0].rule_id, alerts[0].evidence.out_48h_incl_this, alerts[0].evidence.normal_week_outflow, alerts[0].evidence.checks_prior_72h]  

**Case 2224-20250101** (strongest alert: R2 Check far above own baseline)

> Smith Collective LLC (construction, open 572 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R2: a $38,019 check against its usual monthly inflow of $74,974 [alerts[0].rule_id, alerts[0].evidence.amount, alerts[0].evidence.reference_monthly_inflow, alerts[0].evidence.uses_stated_revenue]  

**Case 2377-20250113** (strongest alert: R3 Many new check payers)

> Roberts Studio LLC (education_services, open 6 days) is queued for a document request on 2 alerts [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R3: 11 first-time check payers in a week, far above what is normal in education_services (z-score 5.6) [alerts[0].rule_id, alerts[0].evidence.new_payers_7d, alerts[0].evidence.industry, alerts[0].evidence.new_payers_7d_industry_z]  

**Case 5945-20250102** (strongest alert: R4 First payment to changed bank details)

> King Group LLC (retail, open 675 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R4: first payment, $8,052 (usually $9,369), to a payee whose bank details changed 2.6 days earlier [alerts[0].rule_id, alerts[0].evidence.amount, alerts[0].evidence.days_since_bank_details_change, alerts[0].evidence.payee_median_last6]  

**Case 7385-20250101** (strongest alert: R5 Payment far above usual for payee)

> Frederick Partners LLC (retail, open 397 days) is queued for a document request on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R5: $6,808 to a payee usually paid $573, after 3 earlier payments [alerts[0].rule_id, alerts[0].evidence.amount, alerts[0].evidence.payee_median_last6, alerts[0].evidence.prior_payments_to_payee]  

**Case 1058-20250101** (strongest alert: R6 Applicant shares identity with others)

> Marshall Partners LLC (construction), an applicant whose account would open 2025-01-08, is queued for a document request on 1 alert [business.legal_name, business.industry, business.open_date, case.action, case.alert_count]  
> R6: the application shares address with an earlier applicant; 22 linked applications, 2 of them declined; incorporated 664 days before applying [alerts[0].rule_id, alerts[0].evidence.most_shared_attributes, alerts[0].evidence.linked_applications, alerts[0].evidence.linked_declined_applications, alerts[0].evidence.days_incorporated]  

**Case 170-20250101** (strongest alert: R7 Many new senders, swept out)

> Diaz Collective LLC (education_services, open 745 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R7: 31 first-time senders paid in $5,604 over two weeks, and $19,266 went back out [alerts[0].rule_id, alerts[0].evidence.new_senders_14d, alerts[0].evidence.new_sender_inbound_14d, alerts[0].evidence.out_14d_incl_this]  

**Case 6980-20250217** (strongest alert: R8 New device, contact change, new payee)

> Blair Partners LLC (trucking, open 137 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R8: first payment to a payee added after a login from a new device 8.3 hours earlier, with 2 contact change(s) since [alerts[0].rule_id, alerts[0].evidence.hours_since_new_device, alerts[0].evidence.contact_changes_since_new_device]  

**Case 1681-20250101** (strongest alert: R9 ACH debit money out fast)

> Marsh Group LLC (restaurant, open 551 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R9: $19,310 went out in two days against a normal week of $16,135, right after $6,030 pulled in by ACH debit [alerts[0].rule_id, alerts[0].evidence.out_48h_incl_this, alerts[0].evidence.normal_week_outflow, alerts[0].evidence.ach_debits_prior_5d]  

**Case 8795-20250101** (strongest alert: R10 Inflows ramped before a credit decision)

> Stephens Studio LLC (professional_services, open 210 days) is queued for a document request on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R10: a credit request after $24,237 came in over the last month, against $9,571 a month before; 54% of it from new payers [alerts[0].rule_id, alerts[0].evidence.inflow_last_30d, alerts[0].evidence.baseline_monthly_inflow_31_120d, alerts[0].evidence.share_last_30d_from_new_payers]  

**Case 6173-20250108** (strongest alert: R11 Credit draw money out fast)

> King Supply LLC (retail, open 1301 days) is queued for a hold on 2 alerts [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R11: $7,094 went out in two days against a normal week of $3,538, right after $3,875 drawn on the credit line [alerts[0].rule_id, alerts[0].evidence.out_48h_incl_this, alerts[0].evidence.normal_week_outflow, alerts[0].evidence.line_draws_prior_72h]  

**Case 6511-20250425** (strongest alert: R12 Line drawn to limit soon after increase)

> Davis Co LLC (restaurant, open 598 days) is queued for a hold on 1 alert [business.legal_name, business.industry, business.tenure_days, case.action, case.alert_count]  
> R12: a $130,009 draw takes the line to 97% of its $150,000 limit, raised 7.5 days ago [alerts[0].rule_id, alerts[0].evidence.amount, alerts[0].evidence.utilisation_after, alerts[0].evidence.current_limit, alerts[0].evidence.days_since_limit_increase]  
<!-- summary-examples:end -->

## The guardrail, measured

The check rejects a line that cites nothing, cites a field the case does not have, names a rule none of its
fields belongs to, or states a number or date that none of its cited fields holds. To measure it, the summaries of
500 sampled cases were corrupted in known ways.

<!-- summary-checks:start -->
| Summaries checked | Should the check reject them? | Summaries | Rejected | Rejection rate |
|---|---|---|---|---|
| Summaries as the `template` writer wrote them | no (they should all pass) | 27,242 | 0 | 0.00% |
| added an invented claim, uncited | yes | 500 | 500 | 100.0% |
| changed a number | yes | 500 | 500 | 100.0% |
| cited a field the case does not have | yes | 500 | 500 | 100.0% |
| dropped a citation | yes | 500 | 500 | 100.0% |
| named the wrong rule | yes | 500 | 500 | 100.0% |
| added an invented claim with a real citation | no (a known limit) | 500 | 0 | 0.0% |
| swapped two cited numbers | no (a known limit) | 500 | 0 | 0.0% |
<!-- summary-checks:end -->

[What the two misses mean: the check proves traceability, not meaning. An invented sentence that cites a real
field and contains no number passes; so do two cited numbers in each other's places. A reviewer still reads.]

## What it already caught

[Before release the check rejected template lines saying an applicant had been "open -4 days" (applications are
reviewed before the account opens), and it surfaced a generator bug: some accounts had activity before they
opened. Both were fixed (ADR-025).]

## Adding a language model later

[Same interface, key from an environment variable, same check on every line, and this table re-run for the new
writer before it is switched on.]
