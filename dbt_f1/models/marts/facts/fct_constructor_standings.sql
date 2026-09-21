{{ config(materialized='incremental', unique_key='standing_key', incremental_strategy='merge',
          on_schema_change='append_new_columns') }}

select
    business_key as standing_key,
    season || ':' || round_number as race_key,
    season, round_number,
    payload:record:Constructor:constructorId::varchar as constructor_id,
    try_to_number(payload:record:position::varchar) as championship_position,
    payload:record:positionText::varchar as championship_position_text,
    try_to_decimal(payload:record:points::varchar, 10, 2) as championship_points,
    try_to_number(payload:record:wins::varchar) as wins,
    updated_at
from {{ ref('stg_source_records') }}
where dataset = 'constructorstandings'
{% if is_incremental() and not var('reprocess_history', false) %}
  and updated_at >= (select coalesce(max(updated_at), '1900-01-01'::timestamp_tz) from {{ this }})
{% endif %}
