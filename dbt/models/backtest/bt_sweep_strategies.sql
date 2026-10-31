-- Each rule alone at each cutoff in its sweep grid is one "strategy".
select
    s.rule_id || ' @ ' || cast(s.cutoff as varchar) as strategy_id,
    'sweep'                                        as strategy_kind,
    s.rule_id,
    s.cutoff,
    s.cutoff = r.threshold                         as is_champion_cutoff
from {{ ref('cfg_sweep') }} as s
join {{ ref('cfg_rules') }} as r using (rule_id)
