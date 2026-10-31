-- Weekly precision per rule, as it matures. In week W the bank only knows the cases confirmed so far, so
-- monitoring reports precision with labels known within precision_maturity_days of the week closing, next to
-- the eventual (complete) precision. The gap is the label delay (ADR-013).
with graded as (
    select
        g.*,
        cast(date_trunc('week', g.event_time) as date)                                    as week,
        c.label_known_at,
        cast(date_trunc('week', g.event_time) as date) + interval 7 day
            + to_days(cast(m.precision_maturity_days as integer))                          as matures_at
    from {{ ref('bt_rule_hits_graded') }} as g
    cross join {{ ref('cfg_monitoring') }} as m
    left join {{ ref('bt_cases') }} as c using (case_id)
)

select
    week,
    rule_id,
    count(*)                                                                         as alerts,
    count(*) filter (where label <> 'good' and label_known_at <= matures_at)          as fraud_alerts_known_at_maturity,
    count(*) filter (where label <> 'good')                                          as fraud_alerts_eventually
from graded
cross join (select unnest(string_split(rules, ',')) as rule_id) as r
group by week, rule_id
