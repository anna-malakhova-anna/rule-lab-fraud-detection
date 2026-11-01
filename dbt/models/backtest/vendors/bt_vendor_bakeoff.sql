-- The buying question for each vendor and call strategy (module D, ADR-022), test months:
--   incremental lift   fraud dollars prevented on top of today's rules, and cases ONLY the vendor caught
--   false-positive cost  extra good businesses flagged and extra reviews, priced with the stated costs
--   cost                calls x price per call; cost per dollar of fraud prevented; the break-even price per call
--   speed               whether the vendor answers inside a payment's decision budget
with base as (select * from {{ ref('bt_vendor_metrics') }} where strategy_id = 'champion' and period = 'test'),

base_cases as (select case_id from {{ ref('bt_vendor_cases') }} where strategy_id = 'champion' and detected),

unique_catches as (
    select c.strategy_id, count(*) as cases_only_with_vendor
    from {{ ref('bt_vendor_cases') }} as c
    where c.detected and c.period = 'test' and c.case_id not in (select case_id from base_cases)
    group by c.strategy_id
),

joined as (
    select
        s.strategy_id, s.vendor, s.call_strategy, v.vendor_name, v.cost_per_call, v.latency_ms,
        m.loss_prevented - b.loss_prevented                                  as added_fraud_prevented,
        coalesce(u.cases_only_with_vendor, 0)                                as cases_only_with_vendor,
        m.good_businesses_flagged - b.good_businesses_flagged                as added_good_businesses_flagged,
        m.reviews - b.reviews                                                as added_reviews,
        m.reviews_per_day - b.reviews_per_day                                as added_reviews_per_day,
        coalesce(k.calls, 0)                                                 as calls
    from {{ ref('bt_vendor_strategies') }} as s
    join {{ ref('cfg_vendors') }} as v using (vendor)
    join {{ ref('bt_vendor_metrics') }} as m on m.strategy_id = s.strategy_id and m.period = 'test'
    cross join base as b
    left join unique_catches as u on u.strategy_id = s.strategy_id
    left join {{ ref('bt_vendor_calls') }} as k on k.strategy_id = s.strategy_id and k.period = 'test'
    where s.strategy_kind = 'vendor'
)

select
    *,
    calls * cost_per_call                                                          as vendor_cost,
    {{ cost('review_cost') }} * added_reviews
      + {{ cost('good_customer_touch_cost') }} * added_good_businesses_flagged       as false_positive_cost,
    calls * cost_per_call / nullif(added_fraud_prevented, 0)                       as cost_per_dollar_prevented,
    -- The most this vendor could charge per call and still pay for itself here.
    (added_fraud_prevented - {{ cost('review_cost') }} * added_reviews
      - {{ cost('good_customer_touch_cost') }} * added_good_businesses_flagged) / nullif(calls, 0) as break_even_cost_per_call,
    added_fraud_prevented - calls * cost_per_call - {{ cost('review_cost') }} * added_reviews
      - {{ cost('good_customer_touch_cost') }} * added_good_businesses_flagged       as net_value,
    latency_ms <= (select budget_ms from {{ ref('cfg_latency_budget') }} where decision_point = 'payment') as fast_enough_for_payments
from joined
