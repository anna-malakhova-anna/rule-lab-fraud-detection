-- The sweep point at a rule's champion cutoff must reproduce that rule's live hits exactly.
with sweep as (
    select h.rule_id, h.txn_id
    from {{ ref('bt_sweep_hits') }} as h
    join {{ ref('bt_sweep_strategies') }} as s using (strategy_id)
    where s.is_champion_cutoff
),
live as (select rule_id, entity_id as txn_id from {{ ref('rule_hits') }})
(select * from sweep except select * from live)
union all
(select * from live except select * from sweep)
