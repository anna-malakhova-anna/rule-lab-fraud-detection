-- Hits for each bake-off rule set: every champion hit, plus the vendor's hits at the call points that call
-- strategy would have paid for. Same actions as the vendor rule (RFI at onboarding, hold on a payment).
with called_applications as (
    select s.strategy_id, s.strategy_kind, s.rule_id, s.cutoff, c.call_point_id as txn_id, c.business_id,
           a.applied_at as event_time, 'application' as txn_type, 0.0 as amount, c.score, false as escalation_eligible
    from {{ ref('bt_vendor_strategies') }} as s
    join {{ ref('vnd_call_points') }} as c on c.vendor = s.vendor and c.call_point = 'application' and c.covered
    join {{ ref('stg_applications') }} as a on a.application_id = c.call_point_id and a.decision = 'approved'
    where s.strategy_kind = 'vendor'
      and (s.call_strategy in ('always', 'onboarding_only') or c.risk_gated_call)
),

called_payments as (
    select s.strategy_id, s.strategy_kind, s.rule_id, s.cutoff, l.txn_id, any_value(l.business_id) as business_id,
           any_value(l.txn_time) as event_time, any_value(l.txn_type) as txn_type, any_value(l.amount) as amount,
           max(l.score) as score, true as escalation_eligible
    from {{ ref('bt_vendor_strategies') }} as s
    join {{ ref('vnd_payment_links') }} as l on l.vendor = s.vendor
    where s.strategy_kind = 'vendor'
      and (s.call_strategy = 'always' or (s.call_strategy = 'risk_gated' and l.risk_gated_call))
    group by s.strategy_id, s.strategy_kind, s.rule_id, s.cutoff, l.txn_id
),

vendor_hits as (
    select v.*, {{ hit_action('v.score', 'r', 'v.escalation_eligible') }} as action
    from (select * from called_applications union all select * from called_payments) as v
    join {{ ref('cfg_rules') }} as r using (rule_id)
    where {{ passes('v.score', 'r.comparator', 'v.cutoff') }}
)

select s.strategy_id, s.strategy_kind, h.rule_id, r.threshold as cutoff, h.entity_id as txn_id, h.business_id,
       h.event_time, h.txn_type, h.amount, h.action
from {{ ref('bt_vendor_strategies') }} as s
cross join {{ ref('rule_hits') }} as h
join {{ ref('cfg_rules') }} as r on r.rule_id = h.rule_id
where h.status = 'champion'

union all

select strategy_id, strategy_kind, rule_id, cutoff, txn_id, business_id, event_time, txn_type, amount, action
from vendor_hits
