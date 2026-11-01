{# Every rule, in one place. tests/test_rules.py checks this list matches config/rules.yaml. #}
{% macro rule_ids() -%}
{{ return(['R1_check_then_fast_out', 'R2_check_vs_own_baseline', 'R3_many_new_check_payers',
           'R4_new_bank_details_first_payment', 'R5_payee_amount_out_of_pattern',
           'R6_onboarding_shared_identity', 'R7_mule_fan_in_sweep', 'R8_ato_new_device_sequence',
           'R9_ach_pull_then_fast_out', 'R10_credit_inflow_ramp', 'R11_draw_then_fast_out',
           'R12_full_draw_after_increase',
           'C1_instant_new_account', 'C2_instant_new_payee', 'C3_instant_after_contact_change',
           'C4_instant_uncleared_funds',
           'V1_device_vendor', 'V2_contact_vendor', 'V3_registry_vendor']) }}
{%- endmacro %}
