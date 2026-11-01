-- Launch control: an instant payout from a young account goes out the standard way instead.
-- Score: days since the account opened.
select
    'C1_instant_new_account'                  as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    cast(days_since_open as double)           as score,
    true                                      as escalation_eligible,
    json_object('days_since_open', days_since_open, 'amount', amount) as evidence,
    printf('instant payout of $%,.0f from an account opened %d days ago', amount, days_since_open) as detail
from {{ ref('feat_payment_signals') }}
where is_instant
