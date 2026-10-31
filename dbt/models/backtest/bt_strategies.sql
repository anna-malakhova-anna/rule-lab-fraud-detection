-- The two rule SETS compared head to head (champion = config/rules.yaml thresholds; challenger = tuned).
select 'champion' as strategy_id, 'champion' as strategy_kind, cast(null as varchar) as rule_id, cast(null as double) as cutoff
union all
select 'challenger', 'challenger', null, null
