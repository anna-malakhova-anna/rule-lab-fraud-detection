-- Every rule's candidates with their score, BEFORE any threshold: the input to the threshold sweep.
{% for r in rule_ids() %}
select rule_id, txn_id, business_id, event_time, txn_type, amount, score from {{ ref('cand_' ~ r) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
