-- Loss-level credit for every rule set: per loss transaction, the share of it the rule set prevented. Read by the
-- launch review (module C, ADR-021) and the quarterly rule review's leave-one-out value (module F, ADR-024).
{{ loss_credit(ref('bt_strategy_graded'), ref('bt_strategies')) }}
