-- The rule SETS compared head to head:
--   champion         running today
--   challenger       champion + the proposed rules (the current recommendation)
--   launch_controls  champion + every instant-payout launch control (module C)
--   launch:<rule>    champion + one launch control, to see what each control is worth on its own
--   fast_lane:<cap>  challenger, softened for established, clean businesses on amounts below the cap (module E);
--                    fast_lane:none softens at any amount
--   fast_lane_clear_all  challenger with every alert on a fast-lane business dropped: the cautionary version
--   decline_at:<n>   challenger with R6 declining at score n instead of 3; decline_at:never declines nobody
--   without:<rule>   challenger minus one rule: what that rule adds on top of the others (module F)
select 'champion' as strategy_id, 'champion' as strategy_kind, cast(null as varchar) as rule_id, cast(null as double) as cutoff
union all
select 'challenger', 'challenger', null, null
union all
select 'launch_controls', 'launch_controls', null, null
union all
select 'launch:' || rule_id, 'launch_control_alone', rule_id, threshold
from {{ ref('cfg_rules') }}
where status = 'launch_control'
union all
select 'fast_lane:' || coalesce(cast(cast(max_amount as integer) as varchar), 'none'), 'fast_lane', null, max_amount
from {{ ref('cfg_fast_lane_caps') }}
union all
select 'fast_lane_clear_all', 'fast_lane_clear_all', null, null
union all
select 'decline_at:' || coalesce(cast(cast(decline_at as integer) as varchar), 'never'), 'decline_bar',
       'R6_onboarding_shared_identity', decline_at
from {{ ref('cfg_decline_bar') }}
union all
select 'without:' || rule_id, 'leave_one_out', rule_id, null
from {{ ref('cfg_rules') }}
where status in ('champion', 'challenger')
