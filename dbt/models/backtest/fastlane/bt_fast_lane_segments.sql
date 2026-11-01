-- Where the recommended rules (the challenger) raise mostly false alarms (module E): precision by segment, per
-- rule and for all rules together. Two cuts: fast-lane status (established and clean, ADR-023) and industry.
-- Industry is shown for discovery only; with few fraud cases per industry it is too thin to set policy on.
with hits as (
    select
        g.period, g.label, g.txn_id, g.business_id, g.event_time, g.hold_days,
        unnest(string_split(g.rules, ',')) as rule_id
    from {{ ref('bt_strategy_graded') }} as g
    where g.strategy_id = 'challenger' and g.period in ('train', 'test')
),

segmented as (
    select
        h.*,
        b.industry,
        case when {{ in_fast_lane('h.business_id', 'h.event_time') }} then 'established, clean' else 'everyone else' end as fast_lane
    from hits as h
    join {{ ref('stg_businesses') }} as b using (business_id)
),

by_segment as (
    select 'fast_lane' as segment_type, fast_lane as segment, period, rule_id, txn_id, business_id, label, hold_days from segmented
    union all
    select 'industry', industry, period, rule_id, txn_id, business_id, label, hold_days from segmented
)

select
    segment_type,
    segment,
    period,
    coalesce(rule_id, 'all')                                                    as rule_id,
    count(distinct txn_id)                                                      as alerts,
    count(distinct txn_id) filter (where label <> 'good')                       as alerts_on_fraud,
    count(distinct txn_id) filter (where label <> 'good') / count(distinct txn_id) as precision,
    count(distinct txn_id) filter (where label = 'good' and hold_days > 0)      as good_holds,
    count(distinct business_id) filter (where label = 'good')                   as good_businesses_flagged
from by_segment
group by grouping sets ((segment_type, segment, period, rule_id), (segment_type, segment, period))
