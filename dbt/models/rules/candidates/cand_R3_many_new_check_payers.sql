-- Check deposits arriving while the business is suddenly being paid by many payers it has never seen,
-- scored against its own industry (education services take many small checks; trucking firms do not).
select
    'R3_many_new_check_payers'                as rule_id,
    txn_id,
    business_id,
    txn_time                                  as event_time,
    'mobile_check_deposit'                    as txn_type,
    amount,
    new_payers_7d_industry_z                  as score,
    printf('%d first-time payers in 7 days (%s)', new_payers_7d, industry) as detail
from {{ ref('feat_check_deposits') }}
where new_payers_7d >= {{ rule_param('R3_many_new_check_payers', 'min_new_payers') }}
  and new_payers_7d_industry_z is not null
