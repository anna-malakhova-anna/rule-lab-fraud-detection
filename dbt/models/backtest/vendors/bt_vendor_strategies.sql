-- The vendor bake-off's rule sets (module D, ADR-022): today's rules (champion) alone, and today's rules plus one
-- vendor under one call strategy.
with call_strategies as (
    select * from (values ('always'), ('onboarding_only'), ('risk_gated')) as t(call_strategy)
)

select 'champion' as strategy_id, 'champion' as strategy_kind, cast(null as varchar) as rule_id,
       cast(null as double) as cutoff, cast(null as varchar) as vendor, cast(null as varchar) as call_strategy
union all
select 'vendor:' || v.vendor || ':' || cs.call_strategy, 'vendor', v.rule_id, r.threshold, v.vendor, cs.call_strategy
from {{ ref('cfg_vendors') }} as v
join {{ ref('cfg_rules') }} as r using (rule_id)
cross join call_strategies as cs
-- A vendor that only answers at onboarding has nothing more to add with "always"; keep the plan list honest.
where not (cs.call_strategy = 'always' and v.vendor = 'larchstone')
