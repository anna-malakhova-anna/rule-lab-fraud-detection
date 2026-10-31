-- One row per business per active day: money in and out (internal transfers excluded), then rolling
-- 1/7/30-day velocity and a trailing 90-day baseline that ends the day BEFORE, so a day never sets its own baseline.
with daily as (
    select
        business_id,
        txn_date                                                          as activity_date,
        coalesce(sum(amount) filter (where direction = 'in'), 0)          as in_amount,
        count(*) filter (where direction = 'in')                          as in_count,
        coalesce(sum(amount) filter (where direction = 'out'), 0)         as out_amount,
        count(*) filter (where direction = 'out')                         as out_count,
        coalesce(sum(amount) filter (where is_check_deposit), 0)          as check_amount,
        count(*) filter (where is_check_deposit)                          as check_count
    from {{ ref('stg_transactions') }}
    where not is_internal
    group by business_id, txn_date
)

select
    d.*,
    sum(in_amount)  over w7  as in_amount_7d,
    sum(in_count)   over w7  as in_count_7d,
    sum(out_amount) over w7  as out_amount_7d,
    sum(out_count)  over w7  as out_count_7d,
    sum(in_amount)  over w30 as in_amount_30d,
    sum(in_count)   over w30 as in_count_30d,
    sum(out_amount) over w30 as out_amount_30d,
    sum(out_count)  over w30 as out_count_30d,
    -- Trailing baseline: the 90 days before today, scaled to a 30.4-day month.
    coalesce(sum(in_amount)  over w_base, 0) / 90 * 30.4 as baseline_monthly_inflow,
    coalesce(sum(out_amount) over w_base, 0) / 90 * 30.4 as baseline_monthly_outflow,
    -- Current week against the account's own baseline week (null while there is no baseline).
    sum(out_amount) over w7 / nullif(coalesce(sum(out_amount) over w_base, 0) / 90 * 7, 0) as out_7d_vs_baseline,
    sum(in_amount)  over w7 / nullif(coalesce(sum(in_amount)  over w_base, 0) / 90 * 7, 0) as in_7d_vs_baseline
from daily as d
window
    w7     as (partition by business_id order by activity_date range between interval 6 days preceding and current row),
    w30    as (partition by business_id order by activity_date range between interval 29 days preceding and current row),
    w_base as (partition by business_id order by activity_date range between interval 90 days preceding and interval 1 day preceding)
