{{ config(materialized='incremental', unique_key='qualifying_key', incremental_strategy='merge') }}

select
    business_key as qualifying_key,
    season || ':' || round_number as race_key,
    season, round_number,
    payload:record:Driver:driverId::varchar as driver_id,
    payload:record:Constructor:constructorId::varchar as constructor_id,
    try_to_number(payload:record:position::varchar) as qualifying_position,
    payload:record:Q1::varchar as q1_time,
    payload:record:Q2::varchar as q2_time,
    payload:record:Q3::varchar as q3_time,
    updated_at
from {{ ref('stg_source_records') }}
where dataset = 'qualifying'
{% if is_incremental() %}
  and updated_at >= (select coalesce(max(updated_at), '1900-01-01'::timestamp_tz) from {{ this }})
{% endif %}
