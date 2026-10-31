{# A rule's fixed gate, read from config (config/rules.yaml -> seed cfg_rule_params). #}
{% macro rule_param(rule_id, param) -%}
    (select value from {{ ref('cfg_rule_params') }} where rule_id = '{{ rule_id }}' and param = '{{ param }}')
{%- endmacro %}

{# Does a score pass a cutoff, in the rule's own direction (">=" or "<="). #}
{% macro passes(score, comparator, cutoff) -%}
    case {{ comparator }} when '>=' then {{ score }} >= {{ cutoff }} when '<=' then {{ score }} <= {{ cutoff }} end
{%- endmacro %}

{% macro window_value(column) -%}
    (select {{ column }} from {{ ref('cfg_window') }})
{%- endmacro %}

{% macro cost(name) -%}
    (select value from {{ ref('cfg_costs') }} where cost = '{{ name }}')
{%- endmacro %}
