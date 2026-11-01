-- Launch control: no instant payout to a payee added, or whose bank details changed, very recently.
-- Score: hours since the payee was created or its details last changed, whichever is later.
select
    'C2_instant_new_payee'                    as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    24 * least(days_since_payee_created, coalesce(days_since_bank_details_change, days_since_payee_created)) as score,
    true                                      as escalation_eligible,
    json_object('days_since_payee_created', days_since_payee_created,
                'days_since_bank_details_change', days_since_bank_details_change, 'amount', amount) as evidence,
    printf('instant payout of $%,.0f to a payee added or changed %.1f days ago', amount,
           least(days_since_payee_created, coalesce(days_since_bank_details_change, days_since_payee_created))) as detail
from {{ ref('feat_payment_signals') }}
where is_instant and days_since_payee_created is not null
