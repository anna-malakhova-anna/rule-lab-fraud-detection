-- Threat model (module C): for each fraud type, how its cash-out moved to instant payouts after launch, and what
-- that did to today's rules (champion) with and without launch controls. Test months only, before vs after launch.
select
    l.strategy_id,
    c.typology,
    case when cast(l.txn_time as date) < {{ window_value('instant_launch_date') }} then 'before launch' else 'after launch' end
                                                                   as launch_phase,
    count(*)                                                       as loss_payments,
    count(*) filter (where l.is_instant)                           as instant_loss_payments,
    sum(l.loss_amount)                                             as loss_at_stake,
    coalesce(sum(l.loss_amount) filter (where l.is_instant), 0)    as loss_at_stake_instant,
    sum(l.loss_amount * l.prevents)                                as loss_prevented,
    sum(l.loss_amount * l.prevents) / nullif(sum(l.loss_amount), 0) as share_prevented
from {{ ref('bt_launch_loss_credit') }} as l
join {{ ref('bt_cases') }} as c using (case_id)
where cast(l.txn_time as date) >= {{ window_value('train_end') }}
  and l.strategy_id in ('champion', 'launch_controls')
group by all
