-- One row per transaction, with the flags features need. Internal transfers between a business's own
-- sub-accounts move no money in or out of the business, so they are excluded from velocity.
select
    t.txn_id,
    t.account_id,
    t.business_id,
    t.txn_time,
    cast(t.txn_time as date)                                       as txn_date,
    t.txn_type,
    t.direction,
    t.amount,
    t.counterparty_id,
    t.payee_id,
    t.bank_details_id,
    t.txn_type like 'internal_transfer%'                           as is_internal,
    t.txn_type in ('ach_out', 'wire_out', 'payroll', 'instant_payout') as is_payment_out,
    t.txn_type = 'instant_payout'                                  as is_instant,
    t.txn_type = 'mobile_check_deposit'                            as is_check_deposit
from {{ source('raw', 'transactions') }} as t
