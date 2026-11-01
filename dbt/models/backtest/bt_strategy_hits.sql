-- Hits for the rule sets, from the same candidate models.
--   champion   = the rules running today, at their configured cutoffs.
--   challenger = the champion plus the proposed rules: tuned cutoffs where the rule is tuned, the configured
--                cutoff otherwise, and only from the date a rule written after an alarm went live (ADR-014).
--   launch_controls = the champion plus the instant-payout launch controls at their configured cutoffs (ADR-021);
--   launch:<rule>   = the champion plus that one control.
--   fast_lane:<cap>, fast_lane_clear_all, decline_at:<n> = the challenger's hits with one policy changed (ADR-023).
--   without:<rule> = the challenger's hits minus one rule's (ADR-024).
with challenger_cutoffs as (
    select r.rule_id, r.action, r.escalate_action, r.escalate_at, r.comparator,
           coalesce(t.challenger_cutoff, r.threshold) as cutoff
    from {{ ref('cfg_rules') }} as r
    left join {{ ref('bt_challenger_thresholds') }} as t using (rule_id)
    where r.status = 'champion'
       or (r.status = 'challenger' and (not r.tune or t.is_kept))
),

challenger as (
    select
        c.rule_id, cc.cutoff, c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount, c.score,
        c.escalation_eligible, cc.action as base_action, cc.escalate_action, cc.escalate_at, cc.comparator,
        {{ hit_action('c.score', 'cc') }} as action
    from {{ ref('rule_candidates') }} as c
    join challenger_cutoffs as cc using (rule_id)
    left join {{ ref('mon_rule_effective_from') }} as e using (rule_id)
    where {{ passes('c.score', 'cc.comparator', 'cc.cutoff') }}
      and (e.rule_id is null or c.event_time >= e.effective_from)
),

-- Challenger hits on a business that is in the fast lane at the time of the hit.
fast_lane as (
    select txn_id, rule_id
    from challenger as c
    where {{ in_fast_lane('c.business_id', 'c.event_time') }}
)

select
    'champion' as strategy_id, 'champion' as strategy_kind, h.rule_id, r.threshold as cutoff,
    h.entity_id as txn_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r using (rule_id)
where h.status = 'champion'

union all

select 'challenger', 'challenger', rule_id, cutoff, txn_id, business_id, event_time, txn_type, amount, action
from challenger

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

union all

-- Fast lane: a softened rule acts at most at soften_to on a fast-lane business, below the cap.
select
    s.strategy_id, s.strategy_kind, c.rule_id, c.cutoff, c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount,
    case when fl.txn_id is not null and fr.rule_id is not null and a.severity > soft.severity
              and (s.cutoff is null or c.amount < s.cutoff)
         then soft.action else c.action end
from {{ ref('bt_strategies') }} as s
cross join challenger as c
join {{ ref('cfg_actions') }} as a on a.action = c.action
cross join (select x.action, x.severity from {{ ref('cfg_actions') }} as x
            join {{ ref('cfg_fast_lane') }} as f on f.soften_to = x.action) as soft
left join {{ ref('cfg_fast_lane_rules') }} as fr on fr.rule_id = c.rule_id
left join fast_lane as fl on fl.txn_id = c.txn_id and fl.rule_id = c.rule_id
where s.strategy_kind = 'fast_lane'

union all

-- The cautionary version: every alert on a fast-lane business dropped.
select 'fast_lane_clear_all', 'fast_lane_clear_all', c.rule_id, c.cutoff, c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount, c.action
from challenger as c
where not exists (select 1 from fast_lane as fl where fl.txn_id = c.txn_id and fl.rule_id = c.rule_id)

union all

-- Onboarding decline bar: R6 escalates at the swept score instead of its configured one.
select
    s.strategy_id, s.strategy_kind, c.rule_id, c.cutoff, c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount,
    case when c.rule_id <> s.rule_id then c.action
         when s.cutoff is not null and c.escalation_eligible and {{ passes('c.score', 'c.comparator', 's.cutoff') }}
         then c.escalate_action
         else c.base_action end
from {{ ref('bt_strategies') }} as s
cross join challenger as c
where s.strategy_kind = 'decline_bar'

union all

-- Leave one out: the challenger without one rule.
select s.strategy_id, s.strategy_kind, c.rule_id, c.cutoff, c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount, c.action
from {{ ref('bt_strategies') }} as s
join challenger as c on c.rule_id <> s.rule_id
where s.strategy_kind = 'leave_one_out'
