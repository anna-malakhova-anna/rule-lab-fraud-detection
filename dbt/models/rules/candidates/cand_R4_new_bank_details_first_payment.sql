-- The first payment to a payee's bank details after those details were CHANGED (new payees are not in scope:
-- their first details are the "created" event). Score: days since the change; recent changes are riskier.
select
    'R4_new_bank_details_first_payment'       as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    txn_type,
    amount,
    days_since_bank_details_change            as score,
    printf('first payment to details changed %.1f days ago; $%,.0f (usual $%,.0f)', days_since_bank_details_change,
           amount, coalesce(payee_median_last6, 0)) as detail
from {{ ref('feat_outbound_payments') }}
where bank_details_were_changed
  and is_first_payment_to_bank_details
  and amount >= {{ rule_param('R4_new_bank_details_first_payment', 'min_amount') }}
