-- Every rule's hits at its configured threshold, one row per (rule, entity). `status` says whether the rule
-- runs today (champion) or is proposed (challenger). Entities are transactions, or applications for R6.
{% for r in rule_ids() %}
select * from {{ ref('rule_' ~ r) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
