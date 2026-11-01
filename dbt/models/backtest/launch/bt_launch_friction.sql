-- What the launch controls cost good customers (module C): instant payouts sent the standard way instead, per
-- control, after launch. A good customer's payout arrives about a day later; nothing is refused.
with control_hits as (
    select h.rule_id, h.txn_id, h.business_id, h.amount
    from {{ ref('bt_strategy_hits') }} as h
    join {{ ref('cfg_rules') }} as r using (rule_id)
    where h.strategy_id = 'launch_controls' and r.status = 'launch_control'
),

graded as (
    select txn_id, label from {{ ref('bt_strategy_graded') }} where strategy_id = 'launch_controls'
),

instant as (
    select count(*) as instant_payouts, count(distinct business_id) as businesses_using_instant, sum(amount) as instant_amount
    from {{ ref('stg_transactions') }}
    where is_instant
)

select
    c.rule_id,
    count(*) filter (where g.label = 'good')                        as good_payouts_delayed,
    count(distinct c.business_id) filter (where g.label = 'good')   as good_businesses_delayed,
    coalesce(sum(c.amount) filter (where g.label = 'good'), 0)      as good_amount_delayed,
    count(*) filter (where g.label <> 'good')                       as fraud_payouts_delayed,
    any_value(i.instant_payouts)                                    as instant_payouts,
    any_value(i.businesses_using_instant)                           as businesses_using_instant
from control_hits as c
join graded as g using (txn_id)
cross join instant as i
group by c.rule_id
