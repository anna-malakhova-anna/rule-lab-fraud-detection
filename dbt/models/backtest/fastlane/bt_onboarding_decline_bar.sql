-- Onboarding approval rate (module E): what moving R6's decline bar does to approvals and to fraud, on top of the
-- challenger. decline_at:3 is today's bar (ADR-015) and equals the challenger.
--   applications   every application in the period, including those the bank's existing checks declined
--   approval rate  applications approved by the existing checks and not declined by R6, over all applications
with apps as (
    select
        case when cast(applied_at as date) < {{ window_value('train_end') }} then 'train' else 'test' end as period,
        count(*)                                        as applications,
        count(*) filter (where decision = 'approved')   as approved_before_r6
    from {{ ref('stg_applications') }}
    where cast(applied_at as date) >= {{ window_value('window_start') }}
    group by 1
),

declines as (
    select
        strategy_id,
        period,
        count(*)                                        as declined_by_r6,
        count(*) filter (where label = 'good')          as good_applicants_declined,
        count(*) filter (where label <> 'good')         as fraud_applicants_declined
    from {{ ref('bt_strategy_graded') }}
    where txn_type = 'application' and action = 'block'
    group by strategy_id, period
),

bars as (
    select s.strategy_id, s.cutoff as decline_at, m.period, m.loss_prevented, m.net_value
    from {{ ref('bt_strategies') }} as s
    join {{ ref('bt_strategy_metrics') }} as m using (strategy_id)
    where s.strategy_kind = 'decline_bar' and m.period in ('train', 'test')
)

select
    b.strategy_id,
    b.decline_at,
    b.period,
    a.applications,
    coalesce(d.declined_by_r6, 0)                                           as declined_by_r6,
    coalesce(d.good_applicants_declined, 0)                                 as good_applicants_declined,
    coalesce(d.fraud_applicants_declined, 0)                                as fraud_applicants_declined,
    (a.approved_before_r6 - coalesce(d.declined_by_r6, 0)) / a.applications as approval_rate,
    b.loss_prevented,
    b.net_value,
    today.loss_prevented - b.loss_prevented                                 as fraud_let_through_vs_today,
    b.net_value - today.net_value                                           as net_value_change_vs_today
from bars as b
join apps as a using (period)
left join declines as d using (strategy_id, period)
join bars as today on today.strategy_id = 'decline_at:3' and today.period = b.period
