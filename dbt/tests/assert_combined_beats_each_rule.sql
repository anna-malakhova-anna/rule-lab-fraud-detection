-- Running every champion rule together prevents at least as much as any one of them alone at the same cutoff.
select m.strategy_id, m.period, m.loss_prevented, c.loss_prevented as combined
from {{ ref('bt_sweep_metrics') }} as m
join {{ ref('bt_sweep_strategies') }} as s using (strategy_id)
join {{ ref('bt_strategy_metrics') }} as c on c.strategy_id = 'champion' and c.period = m.period
where s.is_configured_cutoff and s.status = 'champion' and m.loss_prevented > c.loss_prevented + 0.005
