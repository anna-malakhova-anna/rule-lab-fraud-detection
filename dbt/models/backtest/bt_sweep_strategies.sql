-- Each rule alone at each cutoff in its sweep grid is one "strategy". Every rule is swept as written; a rule
-- whose scope the challenger changes (config/rules.yaml challenger_scope, ADR-009) is also swept in that scope.
with scopes as (
    select rule_id, 'as_written' as scope from {{ ref('cfg_rules') }}
    union all
    select distinct rule_id, 'challenger' from {{ ref('cfg_challenger_scope') }}
)

select
    s.rule_id || case sc.scope when 'challenger' then ' [challenger scope]' else '' end
              || ' @ ' || cast(s.cutoff as varchar) as strategy_id,
    'sweep'                                        as strategy_kind,
    s.rule_id,
    sc.scope,
    s.cutoff,
    sc.scope = 'as_written' and s.cutoff = r.threshold as is_champion_cutoff
from {{ ref('cfg_sweep') }} as s
join scopes as sc using (rule_id)
join {{ ref('cfg_rules') }} as r using (rule_id)
