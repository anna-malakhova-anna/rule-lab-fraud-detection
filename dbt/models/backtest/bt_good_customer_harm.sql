-- Who the false positives are: good-customer alerts by hidden archetype (from the answer key), per rule set,
-- rule and period. Shows whether the odd-but-legitimate businesses carry the friction.
with per_rule as (
    select g.*, unnest(string_split(g.rules, ',')) as rule_id
    from {{ ref('bt_strategy_graded') }} as g
    where g.label = 'good' and g.period in ('train', 'test')
)

select
    r.strategy_id,
    r.period,
    r.rule_id,
    p.archetype,
    count(*)                                                as good_alerts,
    count(distinct r.business_id)                           as good_businesses,
    sum(r.amount * r.hold_days)                             as good_dollar_days_held
from per_rule as r
join {{ source('answer_key', 'business_profile') }} as p using (business_id)
group by all
