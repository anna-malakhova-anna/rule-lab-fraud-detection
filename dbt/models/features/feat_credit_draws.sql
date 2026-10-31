-- One row per draw on a line of credit: the limit in force, the balance after the draw, and how recently the
-- limit was raised. The balance is rebuilt from the account's own draws and repayments (running sums).
with line_txns as (
    select
        txn_id, business_id, txn_time, txn_type, amount,
        sum(case when txn_type = 'loc_draw' then amount else -amount end)
            over (partition by business_id order by txn_time, txn_id rows unbounded preceding) as balance_after
    from {{ ref('stg_transactions') }}
    where txn_type in ('loc_draw', 'loc_repayment')
),

limits as (
    select business_id, event_time, event_type, limit_after
    from {{ ref('stg_credit_line_events') }}
    where event_type in ('line_opened', 'limit_increased')
),

-- The limit in force at each draw: the latest opening or increase at or before it.
limit_at_draw as (
    select t.txn_id, l.limit_after as current_limit
    from line_txns as t
    join limits as l on l.business_id = t.business_id and l.event_time <= t.txn_time
    where t.txn_type = 'loc_draw'
    qualify row_number() over (partition by t.txn_id order by l.event_time desc) = 1
),

last_increase as (
    select t.txn_id, max(l.event_time) as last_increase_at
    from line_txns as t
    join limits as l
        on l.business_id = t.business_id and l.event_type = 'limit_increased' and l.event_time <= t.txn_time
    where t.txn_type = 'loc_draw'
    group by t.txn_id
)

select
    t.txn_id,
    t.business_id,
    t.txn_time,
    t.amount,
    la.current_limit,
    greatest(t.balance_after, 0)                                                 as balance_after,
    greatest(t.balance_after, 0) / nullif(la.current_limit, 0)                   as utilisation_after,
    li.last_increase_at,
    date_diff('second', li.last_increase_at, t.txn_time) / 86400.0              as days_since_limit_increase
from line_txns as t
join limit_at_draw as la using (txn_id)
left join last_increase as li using (txn_id)
where t.txn_type = 'loc_draw'
