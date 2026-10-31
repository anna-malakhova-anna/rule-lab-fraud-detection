-- Weekly alarm on each return series: this week's count against the same series' trailing weeks.
-- A week alarms when it has at least min_count returns AND sits more than `sigma` standard deviations above the
-- trailing mean (the deviation is floored at 1, so a series that has been at zero needs min_count to alarm).
-- No fraud labels are used: this is what an analyst could have seen that week.
with weeks as (
    select cast(w as date) as week
    from generate_series(
        cast(date_trunc('week', (select min(week) from {{ ref('mon_weekly_returns') }})) as timestamp),
        cast((select max(week) from {{ ref('mon_weekly_returns') }}) as timestamp),
        interval 7 day) as g(w)
),

series as (select distinct series, txn_type, return_reason from {{ ref('mon_weekly_returns') }}),

-- Every series in every week, zero-filled, so a quiet week counts as a quiet week.
dense as (
    select s.series, s.txn_type, s.return_reason, w.week,
           coalesce(r.returns, 0) as returns, coalesce(r.returned_amount, 0) as returned_amount,
           coalesce(r.unalerted_amount, 0) as unalerted_amount
    from series as s
    cross join weeks as w
    left join {{ ref('mon_weekly_returns') }} as r on r.series = s.series and r.week = w.week
),

cfg as (select * from {{ ref('cfg_monitoring') }}),

-- Self-join: each week against the same series' previous baseline_weeks weeks.
baseline as (
    select
        cur.series,
        cur.week,
        avg(prev.returns)          as baseline_mean,
        stddev_pop(prev.returns)   as baseline_sd,
        count(prev.week)           as baseline_weeks_seen
    from dense as cur
    cross join cfg
    join dense as prev
        on  prev.series = cur.series
        and prev.week <  cur.week
        and prev.week >= cur.week - to_days(cast(cfg.baseline_weeks * 7 as integer))
    group by cur.series, cur.week
)

select
    d.*,
    b.baseline_mean,
    b.baseline_sd,
    d.week + interval 7 day                                                    as week_closes_at,
    d.returns >= cfg.min_count
        and b.baseline_weeks_seen = cfg.baseline_weeks
        and d.returns > b.baseline_mean + cfg.sigma * greatest(b.baseline_sd, 1)  as is_alarm
from dense as d
cross join cfg
join baseline as b using (series, week)
