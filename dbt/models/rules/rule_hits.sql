-- Every rule's hits at champion thresholds, one row per (rule, transaction).
{% set rules = ['R1_check_then_fast_out', 'R2_check_vs_own_baseline', 'R3_many_new_check_payers',
                'R4_new_bank_details_first_payment', 'R5_payee_amount_out_of_pattern'] %}
{% for r in rules %}
select * from {{ ref('rule_' ~ r) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
