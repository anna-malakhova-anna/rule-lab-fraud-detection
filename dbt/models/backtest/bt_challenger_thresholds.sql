-- Challenger cutoffs, chosen on the TRAINING months only (ADR-002, ADR-008):
--   1. a rule whose scope the challenger changes is tuned in that scope (ADR-009); others as written;
--   2. drop cutoffs where the rule alone would use more than its share of daily review capacity;
--   3. keep the cutoff with the highest net value (fraud prevented minus stated costs);
--   4. ties go to the stricter cutoff (fewer alerts).
-- A rule whose best net value is not positive is retired from the challenger.
with train as (
    select m.*, s.scope
    from {{ ref('bt_sweep_metrics') }} as m
    join {{ ref('bt_sweep_strategies') }} as s using (strategy_id)
    where m.period = 'train'
),

in_scope as (
    select t.*
    from train as t
    where t.scope = case when t.rule_id in (select rule_id from {{ ref('cfg_challenger_scope') }})
                         then 'challenger' else 'as_written' end
),

eligible as (
    select *
    from in_scope
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
    scope,
    cutoff                       as challenger_cutoff,
    net_value                    as train_net_value,
    reviews_per_day              as train_reviews_per_day,
    net_value > 0                as is_kept
from ranked
where rnk = 1
