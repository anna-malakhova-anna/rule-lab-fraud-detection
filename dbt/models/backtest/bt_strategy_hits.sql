-- Hits for the champion and challenger rule sets, from the same candidate models.
select
    'champion' as strategy_id, 'champion' as strategy_kind, h.rule_id, r.threshold as cutoff,
    h.entity_id as txn_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r using (rule_id)

union all

select
    'challenger', 'challenger', c.rule_id, t.challenger_cutoff,
    c.txn_id, c.business_id, c.event_time, c.txn_type, c.amount, r.action
from {{ ref('rule_candidates') }} as c
join {{ ref('bt_challenger_thresholds') }} as t using (rule_id)
join {{ ref('cfg_rules') }} as r using (rule_id)
where t.is_kept
  and {{ passes('c.score', 'r.comparator', 't.challenger_cutoff') }}
