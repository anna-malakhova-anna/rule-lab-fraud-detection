-- Hits for the rule sets, from the same candidate models.
--   champion   = the rules running today, at their configured cutoffs.
--   challenger = the champion plus the proposed rules: tuned cutoffs where the rule is tuned, the configured
--                cutoff otherwise, and only from the date a rule written after an alarm went live (ADR-014).
--   launch_controls = the champion plus the instant-payout launch controls at their configured cutoffs (ADR-021);
--   launch:<rule>   = the champion plus that one control.
with challenger_cutoffs as (
    select r.rule_id, r.action, r.escalate_action, r.escalate_at, r.comparator,
           coalesce(t.challenger_cutoff, r.threshold) as cutoff
    from {{ ref('cfg_rules') }} as r
    left join {{ ref('bt_challenger_thresholds') }} as t using (rule_id)
    where r.status = 'champion'
       or (r.status = 'challenger' and (not r.tune or t.is_kept))
)

select
    'champion' as strategy_id, 'champion' as strategy_kind, h.rule_id, r.threshold as cutoff,
    h.entity_id as txn_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r using (rule_id)
where h.status = 'champion'

union all

select
    'challenger', 'challenger', c.rule_id, cc.cutoff,
    c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount, {{ hit_action('c.score', 'cc') }} as action
from {{ ref('rule_candidates') }} as c
join challenger_cutoffs as cc using (rule_id)
left join {{ ref('mon_rule_effective_from') }} as e using (rule_id)
where {{ passes('c.score', 'cc.comparator', 'cc.cutoff') }}
  and (e.rule_id is null or c.event_time >= e.effective_from)

union all

select
    'launch_controls', 'launch_controls', h.rule_id, r.threshold,
    h.entity_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r using (rule_id)
where h.status in ('champion', 'launch_control')

union all

select
    s.strategy_id, s.strategy_kind, h.rule_id, r.threshold,
    h.entity_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('bt_strategies') }} as s
join {{ ref('rule_hits') }} as h on h.status = 'champion' or h.rule_id = s.rule_id
join {{ ref('cfg_rules') }} as r on r.rule_id = h.rule_id
where s.strategy_kind = 'launch_control_alone'
