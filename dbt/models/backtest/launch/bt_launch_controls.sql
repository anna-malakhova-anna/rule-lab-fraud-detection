-- Each launch control on its own and all together, after launch (module C): fraud dollars it adds to today's
-- rules, and the good payouts it sends the slow way. The decision table for the launch review. Net value prices
-- each good business slowed down like any good business flagged (good_customer_touch_cost, ADR-008).
with after_launch as (
    select
        l.strategy_id,
        sum(l.loss_amount)                     as loss_at_stake,
        sum(l.loss_amount * l.prevents)        as loss_prevented
    from {{ ref('bt_loss_credit') }} as l
    where cast(l.txn_time as date) >= {{ window_value('instant_launch_date') }}
    group by l.strategy_id
),

delays as (
    select
        g.strategy_id,
        count(*) filter (where g.label = 'good')                        as good_payouts_delayed,
        count(distinct g.business_id) filter (where g.label = 'good')   as good_businesses_delayed,
        coalesce(sum(g.amount) filter (where g.label = 'good'), 0)      as good_amount_delayed
    from {{ ref('bt_strategy_graded') }} as g
    where g.downgraded_by_control
    group by g.strategy_id
),

base as (select loss_prevented from after_launch where strategy_id = 'champion')

select
    s.strategy_id,
    s.rule_id,
    a.loss_at_stake,
    a.loss_prevented,
    a.loss_prevented - b.loss_prevented                  as added_vs_today,
    coalesce(d.good_payouts_delayed, 0)                  as good_payouts_delayed,
    coalesce(d.good_businesses_delayed, 0)               as good_businesses_delayed,
    coalesce(d.good_amount_delayed, 0)                   as good_amount_delayed,
    a.loss_prevented - b.loss_prevented
      - {{ cost('good_customer_touch_cost') }} * coalesce(d.good_businesses_delayed, 0) as net_value
from {{ ref('bt_strategies') }} as s
cross join base as b
join after_launch as a using (strategy_id)
left join delays as d using (strategy_id)
where s.strategy_id = 'champion' or s.strategy_kind in ('launch_controls', 'launch_control_alone')
