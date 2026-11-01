-- When a business is OUT of the good-customer fast lane (module E, ADR-023): until it has min_tenure_days of
-- history, and for clean_days after any returned item (a bounced check, a returned ACH debit). Bank data only.
-- A business is in the fast lane at time t when no row here covers t (macro in_fast_lane).
select
    business_id,
    cast('1900-01-01' as timestamp)                                                  as excluded_from,
    cast(open_date as timestamp) + to_days(cast((select min_tenure_days from {{ ref('cfg_fast_lane') }}) as integer)) as excluded_until,
    'tenure'                                                                         as reason
from {{ ref('stg_businesses') }}

union all

select
    t.business_id,
    r.return_time,
    r.return_time + to_days(cast((select clean_days from {{ ref('cfg_fast_lane') }}) as integer)),
    'returned_item'
from {{ ref('stg_returns') }} as r
join {{ ref('stg_transactions') }} as t using (txn_id)
