-- How likely an alert from each rule is to be fraud, as the bank knew it when it tuned (end of month 12): the
-- rule's precision on the training months at the cutoff each rule set runs it at, using only labels known by
-- then (ADR-013). This is the "likelihood" half of a case's priority; it never sees the full answer key.
with cutoffs as (
    select distinct strategy_id, rule_id, cutoff from {{ ref('bt_strategy_hits') }}
)

select
    c.strategy_id,
    c.rule_id,
    c.cutoff,
    -- A floor keeps a rule with no known catches yet from ranking at exactly zero.
    greatest(coalesce(m.precision, 0), 0.001)   as likelihood,
    m.alerts                                    as train_alerts,
    m.alerts_on_fraud                           as train_alerts_on_known_fraud
from cutoffs as c
join {{ ref('bt_sweep_strategies') }} as s on s.rule_id = c.rule_id and s.cutoff = c.cutoff
left join {{ ref('bt_sweep_metrics_known') }} as m on m.strategy_id = s.strategy_id and m.period = 'train'
