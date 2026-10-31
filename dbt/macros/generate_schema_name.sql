{# Use the configured schema name as-is (staging, features, rules, backtest), not "<target>_<schema>". #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
