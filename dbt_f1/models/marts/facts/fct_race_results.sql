{{ config(materialized='incremental', unique_key='result_key', incremental_strategy='merge') }}

select
    business_key as result_key,
    season || ':' || round_number as race_key,
    season,
    round_number,
    payload:record:Driver:driverId::varchar as driver_id,
    payload:record:Constructor:constructorId::varchar as constructor_id,
    try_to_number(payload:record:position::varchar) as finishing_position,
    try_to_number(payload:record:grid::varchar) as grid_position,
    try_to_decimal(payload:record:points::varchar, 10, 2) as points,
    try_to_number(payload:record:laps::varchar) as laps_completed,
    try_to_number(payload:record:FastestLap:rank::varchar) as fastest_lap_rank,
    payload:record:status::varchar as status,
    updated_at
from {{ ref('stg_source_records') }}
where dataset = 'results'
{% if is_incremental() %}
  and updated_at >= (select coalesce(max(updated_at), '1900-01-01'::timestamp_tz) from {{ this }})
{% endif %}
