-- Outbound payments made while the account holds a meaningful amount of uncleared check money.
-- Score: the share of that check money that has already left ON TOP of a normal week of the account's spending.
-- (A raw outflow/checks ratio would flag every business that simply spends more than it deposits by check.)
-- Payroll is excluded since Phase 2 (ADR-009, ADR-010).
select
    'R1_check_then_fast_out'                  as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    excess_out_48h_vs_recent_checks           as score,
    true                                      as escalation_eligible,
    json_object('out_48h_incl_this', out_48h_incl_this, 'normal_week_outflow', normal_week_outflow, 'checks_prior_72h', checks_prior_72h) as evidence,
    printf('$%,.0f out in 48h (normal week $%,.0f) vs $%,.0f of checks in 72h',
           out_48h_incl_this, normal_week_outflow, checks_prior_72h) as detail
from {{ ref('feat_outbound_payments') }}
where checks_prior_72h >= {{ rule_param('R1_check_then_fast_out', 'min_recent_checks') }}
  and txn_type <> 'payroll'      -- payroll is out of scope (ADR-009): deposit-fraud money never leaves that way
