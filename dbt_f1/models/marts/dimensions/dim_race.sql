{{ config(materialized='table') }}

select distinct
    business_key as race_key,
    season, round_number, payload:raceName::varchar as race_name,
    payload:date::date as race_date,
    payload:Circuit:circuitId::varchar as circuit_id,
    payload:Circuit:circuitName::varchar as circuit_name,
    payload:Circuit:Location:country::varchar as country
from {{ ref('stg_source_records') }}
where dataset = 'races' and payload:raceName is not null
