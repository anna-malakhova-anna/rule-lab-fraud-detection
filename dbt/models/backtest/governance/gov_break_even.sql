-- The precision a running rule needs to pay for itself (module F, ADR-024), set from the training months at the
-- cutoff it runs at in the recommended rule set (the challenger):
--   value per true alert   fraud dollars the rule prevents on its own / its alerts on fraud
--   cost per false alert   its friction cost on its own (reviews, good customers touched, holds, payrolls,
--                          declines: prevented minus net value) / its alerts on good customers
--   break-even precision   cost / (cost + value): below it, the rule's false alarms cost more than it saves
with running as (
    select distinct rule_id, cutoff from {{ ref('bt_strategy_hits') }} where strategy_id = 'challenger'
)

select
    r.rule_id,
    r.cutoff,
    m.alerts                                                                    as train_alerts,
    m.precision                                                                 as train_precision,
    m.loss_prevented / nullif(m.alerts_on_fraud, 0)                             as value_per_true_alert,
    (m.loss_prevented - m.net_value) / nullif(m.alerts - m.alerts_on_fraud, 0)  as cost_per_false_alert,
    ((m.loss_prevented - m.net_value) / nullif(m.alerts - m.alerts_on_fraud, 0))
      / nullif((m.loss_prevented - m.net_value) / nullif(m.alerts - m.alerts_on_fraud, 0)
               + m.loss_prevented / nullif(m.alerts_on_fraud, 0), 0)            as break_even_precision
from running as r
join {{ ref('bt_sweep_metrics') }} as m
    on m.rule_id = r.rule_id and abs(m.cutoff - r.cutoff) < 1e-9 and m.period = 'train'
