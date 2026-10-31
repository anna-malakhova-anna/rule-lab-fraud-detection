-- Every rule's hits at its configured cutoff, each rule as its own "strategy": the input to per-rule monitoring.
select
    h.rule_id as strategy_id, 'rule' as strategy_kind, h.rule_id, r.threshold as cutoff,
    h.entity_id as txn_id, h.business_id, h.event_time, h.txn_type, h.amount, h.action
from {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r using (rule_id)
