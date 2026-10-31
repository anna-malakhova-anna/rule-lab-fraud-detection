-- Every rule's candidates at every sweep cutoff. Built from the SAME candidate models the live rules use,
-- so a sweep point at the champion cutoff reproduces that rule's hits exactly (a test checks this).
-- In the challenger scope, transaction types the challenger excludes for that rule are dropped.
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
    r.action
from {{ ref('rule_candidates') }} as c
join {{ ref('bt_sweep_strategies') }} as st using (rule_id)
join {{ ref('cfg_rules') }} as r using (rule_id)
where {{ passes('c.score', 'r.comparator', 'st.cutoff') }}
  and not (st.scope = 'challenger' and exists (
        select 1 from {{ ref('cfg_challenger_scope') }} as x
        where x.rule_id = c.rule_id and x.excluded_txn_type = c.txn_type))
