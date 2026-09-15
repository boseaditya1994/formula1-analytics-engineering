{% macro generate_schema_name(custom_schema_name, node) -%}
    {# This single-environment portfolio uses explicitly provisioned schemas. #}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif node.resource_type == 'test' -%}
        {{ target.schema }}
    {%- elif custom_schema_name | trim | upper in ['STAGING', 'INTERMEDIATE', 'MARTS'] -%}
        {{ custom_schema_name | trim | upper }}
    {%- else -%}
        {{ exceptions.raise_compiler_error('Unsupported project schema: ' ~ custom_schema_name) }}
    {%- endif -%}
{%- endmacro %}
