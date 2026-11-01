-- The fast lane's two sides (module E, ADR-023), against the challenger it is built on, at each amount cap:
--   friction removed   good customers' holds avoided, and the hours their money would have waited
--   fraud let through  fraud dollars the challenger stopped and this rule set does not
--   fraud let through per hold avoided: what each avoided hold costs in fraud, the price of a hold to judge
with friction as (
    select
        strategy_id,
        period,
        count(*) filter (where label = 'good' and hold_days > 0)               as good_holds,
        coalesce(sum(hold_days * 24) filter (where label = 'good'), 0)         as good_customer_hours_held
    from {{ ref('bt_strategy_graded') }}
    where (strategy_id = 'challenger' or strategy_id like 'fast_lane%') and period in ('train', 'test')
    group by strategy_id, period
),

metrics as (
    select m.*, f.good_holds, f.good_customer_hours_held
    from {{ ref('bt_strategy_metrics') }} as m
    join friction as f using (strategy_id, period)
)

select
    m.strategy_id,
    m.strategy_kind,
    m.cutoff                                                        as max_amount,
    m.period,
    m.loss_prevented,
    m.dollar_recall,
    m.alerts,
    m.reviews,
    m.good_businesses_held,
    m.good_holds,
    m.good_customer_hours_held,
    m.net_value,
    base.good_holds - m.good_holds                                  as good_holds_avoided,
    base.good_customer_hours_held - m.good_customer_hours_held      as customer_hours_saved,
    base.good_businesses_held - m.good_businesses_held              as good_businesses_no_longer_held,
    base.reviews - m.reviews                                        as reviews_saved,
    base.loss_prevented - m.loss_prevented                          as fraud_let_through,
    m.net_value - base.net_value                                    as net_value_change,
    (base.loss_prevented - m.loss_prevented) / nullif(base.good_holds - m.good_holds, 0) as fraud_let_through_per_hold_avoided
from metrics as m
join metrics as base on base.strategy_id = 'challenger' and base.period = m.period
