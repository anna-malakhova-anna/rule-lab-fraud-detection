-- The rule SETS compared head to head:
--   champion         running today
--   challenger       champion + the proposed rules
--   launch_controls  champion + every instant-payout launch control (module C)
--   launch:<rule>    champion + one launch control, to see what each control is worth on its own
select 'champion' as strategy_id, 'champion' as strategy_kind, cast(null as varchar) as rule_id, cast(null as double) as cutoff
union all
select 'challenger', 'challenger', null, null
union all
select 'launch_controls', 'launch_controls', null, null
union all
select 'launch:' || rule_id, 'launch_control_alone', rule_id, threshold
from {{ ref('cfg_rules') }}
where status = 'launch_control'
