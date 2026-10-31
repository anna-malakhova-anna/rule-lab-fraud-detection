-- Returned payments per week, by rail and return reason: data the bank sees as soon as a return arrives,
-- with no fraud labels involved. "Unalerted" returns are on businesses no champion rule flagged between 30
-- days before the returned transaction and the return itself: losses arriving that the rules never saw.
with returns as (
    select r.return_id, r.return_time, r.return_reason, t.txn_id, t.txn_type, t.business_id, t.amount, t.txn_time
    from {{ ref('stg_returns') }} as r
    join {{ ref('stg_transactions') }} as t using (txn_id)
),

champion_alerts as (
    select business_id, event_time from {{ ref('rule_hits') }} where status = 'champion'
),

flagged as (
    select
        r.*,
        exists (
            select 1 from champion_alerts as a
            where a.business_id = r.business_id
              and a.event_time between r.txn_time - interval 30 day and r.return_time
        ) as was_alerted
    from returns as r
)

select
    cast(date_trunc('week', return_time) as date)                  as week,
    txn_type || ':' || return_reason                                as series,
    txn_type,
    return_reason,
    count(*)                                                        as returns,
    sum(amount)                                                     as returned_amount,
    count(*) filter (where not was_alerted)                         as unalerted_returns,
    coalesce(sum(amount) filter (where not was_alerted), 0)         as unalerted_amount
from flagged
group by all
