-- Every rule's candidates at every sweep cutoff. Built from the SAME candidate models the live rules use,
-- so a sweep point at the configured cutoff reproduces that rule's hits exactly (a test checks this).
select
    st.strategy_id,
    st.strategy_kind,
    c.rule_id,
    st.cutoff,
    c.txn_id,
    c.business_id,
    c.event_time,
    c.txn_type,
    c.amount,
    {{ hit_action('c.score') }} as action
from {{ ref('rule_candidates') }} as c
join {{ ref('bt_sweep_strategies') }} as st using (rule_id)
join {{ ref('cfg_rules') }} as r using (rule_id)
where {{ passes('c.score', 'r.comparator', 'st.cutoff') }}
