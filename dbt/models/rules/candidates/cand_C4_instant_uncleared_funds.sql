-- Launch control: an instant payout funded by money that can still come back (checks in the last 72 hours, ACH
-- debits in the last 5 days, credit-line draws in the last 72 hours). Score: that money / the payout amount.
select
    'C4_instant_uncleared_funds'              as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    (checks_prior_72h + ach_debits_prior_5d + line_draws_prior_72h) / nullif(amount, 0) as score,
    true                                      as escalation_eligible,
    json_object('checks_prior_72h', checks_prior_72h, 'ach_debits_prior_5d', ach_debits_prior_5d,
                'line_draws_prior_72h', line_draws_prior_72h, 'amount', amount) as evidence,
    printf('instant payout of $%,.0f with $%,.0f of returnable money received in the last few days', amount,
           checks_prior_72h + ach_debits_prior_5d + line_draws_prior_72h) as detail
from {{ ref('feat_payment_signals') }}
where is_instant and checks_prior_72h + ach_debits_prior_5d + line_draws_prior_72h > 0
