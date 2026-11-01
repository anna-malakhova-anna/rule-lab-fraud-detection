-- Rule blind spots (module C): loss each running rule stopped BEFORE launch only by alerting on the cash-out
-- payment itself, with no earlier alert on the case. On instant payouts that alert comes too late, so this is
-- what each rule stops catching once cash-outs go instant (ADR-021). Every graded month before launch, champion.
with loss as (
    select l.*
    from {{ ref('bt_launch_loss_credit') }} as l
    where l.strategy_id = 'champion'
      and cast(l.txn_time as date) >= {{ window_value('window_start') }}
      and cast(l.txn_time as date) <  {{ window_value('instant_launch_date') }}
      and l.prevents > 0
),

-- Was there any alert on the case strictly before this payment?
earlier as (
    select l.txn_id, bool_or(g.event_time < l.txn_time) as had_earlier_alert
    from loss as l
    join {{ ref('bt_strategy_graded') }} as g
        on g.strategy_id = 'champion' and g.case_id = l.case_id and g.event_time <= l.txn_time
    group by l.txn_id
),

on_payment as (
    select l.txn_id, l.loss_amount * l.prevents as stopped, unnest(string_split(g.rules, ',')) as rule_id
    from loss as l
    join earlier as e using (txn_id)
    join {{ ref('bt_strategy_graded') }} as g on g.strategy_id = 'champion' and g.txn_id = l.txn_id
    where not e.had_earlier_alert
)

select
    r.rule_id,
    r.reason_code,
    coalesce(sum(o.stopped), 0)          as stopped_only_at_the_payment,
    count(distinct o.txn_id)             as payments
from {{ ref('cfg_rules') }} as r
left join on_payment as o using (rule_id)
where r.status = 'champion'
group by all
