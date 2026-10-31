{#
  Turn a rule's candidates into hits at the champion threshold from config/rules.yaml.
  Output contract (every rule): rule_id, entity_id, event_time, action, reason, plus context columns.
#}
{% macro rule_hits(rule_id) -%}
select
    c.rule_id,
    c.txn_id                       as entity_id,
    c.event_time,
    {{ hit_action('c.score') }} as action,
    printf('%s: %s = %.2f (cutoff %s %s)', c.rule_id, r.score_description, c.score, r.comparator, cast(r.threshold as varchar))
        || coalesce('; ' || c.detail, '') as reason,
    r.status,
    c.business_id,
    c.txn_type,
    c.amount,
    c.score,
    c.escalation_eligible
from {{ ref('cand_' ~ rule_id) }} as c
join {{ ref('cfg_rules') }} as r using (rule_id)
where {{ passes('c.score', 'r.comparator', 'r.threshold') }}
{%- endmacro %}
