-- Challenger cutoffs, chosen on the TRAINING months only (ADR-002, ADR-008):
--   1. drop cutoffs where the rule alone would use more than its share of daily review capacity;
--   2. keep the cutoff with the highest net value (fraud prevented minus stated costs);
--   3. ties go to the stricter cutoff (fewer alerts).
-- A rule whose best net value is not positive is retired from the challenger.
with train as (
    select m.*, r.comparator
    from {{ ref('bt_sweep_metrics') }} as m
    join {{ ref('cfg_rules') }} as r using (rule_id)
    where m.period = 'train'
),

eligible as (
    select *
    from train
    where reviews_per_day <= {{ window_value('reviews_capacity_per_day') }} * {{ cost('max_capacity_share_per_rule') }}
),

ranked as (
    select
        *,
        row_number() over (partition by rule_id order by net_value desc, alerts asc) as rnk
    from eligible
)

select
    rule_id,
    cutoff                       as challenger_cutoff,
    net_value                    as train_net_value,
    reviews_per_day              as train_reviews_per_day,
    net_value > 0                as is_kept
from ranked
where rnk = 1
