-- Alert volume per champion rule per week: the first thing to watch after any rule change.
select
    cast(date_trunc('week', event_time) as date)  as week,
    rule_id,
    count(*)                                       as alerts,
    count(distinct business_id)                    as businesses_alerted
from {{ ref('rule_hits') }}
where status = 'champion'
group by all
