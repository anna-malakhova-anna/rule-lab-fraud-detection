-- Reviews per business day for champion and challenger, against capacity. Days with no alerts count as zero.
with daily as (
    select strategy_id, review_date, count(distinct business_id) as reviews
    from {{ ref('bt_strategy_graded') }}
    where is_review
    group by strategy_id, review_date
)

select
    s.strategy_id,
    bd.business_date,
    bd.period,
    coalesce(d.reviews, 0)                                              as reviews,
    {{ window_value('reviews_capacity_per_day') }}                      as capacity,
    coalesce(d.reviews, 0) > {{ window_value('reviews_capacity_per_day') }} as over_capacity
from {{ ref('bt_strategies') }} as s
cross join {{ ref('bt_business_days') }} as bd
left join daily as d on d.strategy_id = s.strategy_id and d.review_date = bd.business_date
