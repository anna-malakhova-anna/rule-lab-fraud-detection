-- The separate credit-loss line (ADR-016): honest businesses that failed and defaulted on their line. These are
-- NOT fraud and never count as fraud prevented. Reported per rule set: how much was charged off, how much of it
-- sat on businesses a rule had flagged in the 90 days before the missed payment (an early warning, not a
-- prevention), and the friction the rules put on these honest customers while they were struggling.
with failing as (
    select p.business_id
    from {{ source('answer_key', 'business_profile') }} as p
    where p.archetype = 'failing_business'
),

defaults as (
    select
        e.business_id,
        min(e.event_time) filter (where e.event_type = 'payment_missed')   as missed_at,
        max(e.balance)    filter (where e.event_type = 'payment_missed')   as balance_at_missed,
        max(e.balance)    filter (where e.event_type = 'charged_off')      as charged_off_balance
    from {{ ref('stg_credit_line_events') }} as e
    join failing using (business_id)
    group by e.business_id
),

per_strategy as (
    select
        s.strategy_id,
        d.business_id,
        d.missed_at,
        d.balance_at_missed,
        d.charged_off_balance,
        exists (
            select 1 from {{ ref('bt_strategy_graded') }} as g
            where g.strategy_id = s.strategy_id and g.business_id = d.business_id
              and g.event_time between d.missed_at - interval 90 day and d.missed_at
        ) as flagged_before_default,
        (select count(*) from {{ ref('bt_strategy_graded') }} as g
         where g.strategy_id = s.strategy_id and g.business_id = d.business_id and g.hold_days > 0) as holds_on_this_business
    from {{ ref('bt_strategies') }} as s
    cross join defaults as d
    where d.missed_at is not null
)

select
    strategy_id,
    case when cast(missed_at as date) < {{ window_value('train_end') }} then 'train' else 'test' end as period,
    count(*)                                                            as honest_defaults,
    coalesce(sum(charged_off_balance), 0)                               as charged_off_in_window,
    coalesce(sum(balance_at_missed), 0)                                 as balance_at_missed_payment,
    count(*) filter (where flagged_before_default)                      as flagged_before_default,
    coalesce(sum(balance_at_missed) filter (where flagged_before_default), 0) as balance_flagged_before_default,
    sum(holds_on_this_business)                                         as holds_on_honest_defaulters
from per_strategy
group by all
