-- Every weekly series monitoring watches, in one shape: returned payments by rail and return reason, and credit
-- line events (missed payments, charge-offs). All of it is data the bank has the week it happens, no labels.
select
    week,
    series,
    returns                 as events,
    returned_amount         as amount,
    unalerted_amount
from {{ ref('mon_weekly_returns') }}

union all

select
    cast(date_trunc('week', event_time) as date)                   as week,
    'credit:' || event_type                                         as series,
    count(*)                                                        as events,
    coalesce(sum(balance), 0)                                       as amount,
    -- Credit losses on businesses no champion rule flagged in the 90 days before.
    coalesce(sum(balance) filter (where not exists (
        select 1 from {{ ref('rule_hits') }} as h
        where h.status = 'champion' and h.business_id = e.business_id
          and h.event_time between e.event_time - interval 90 day and e.event_time)), 0) as unalerted_amount
from {{ ref('stg_credit_line_events') }} as e
where event_type in ('payment_missed', 'charged_off')
group by all
