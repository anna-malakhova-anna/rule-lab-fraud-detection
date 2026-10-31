-- R1's logic on the ACH-debit rail (ADR-014): outbound payments made while money pulled in by ACH debit in the
-- last 5 days can still come back, scored by the share of it that already left on top of a normal week.
select
    'R9_ach_pull_then_fast_out'               as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    excess_out_48h_vs_ach_debits              as score,
    true                                      as escalation_eligible,
    printf('$%,.0f out in 48h (normal week $%,.0f) vs $%,.0f pulled by ACH debit in 5 days',
           out_48h_incl_this, normal_week_outflow, ach_debits_prior_5d) as detail
from {{ ref('feat_payment_signals') }}
where txn_type <> 'payroll'
  and ach_debits_prior_5d >= {{ rule_param('R9_ach_pull_then_fast_out', 'min_recent_pulls') }}
