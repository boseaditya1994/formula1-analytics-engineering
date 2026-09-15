{{ config(materialized='table') }}

select
    payload:Circuit:circuitId::varchar as circuit_id,
    payload:Circuit:circuitName::varchar as circuit_name,
    payload:Circuit:Location:locality::varchar as locality,
    payload:Circuit:Location:country::varchar as country,
    try_to_double(payload:Circuit:Location:lat::varchar) as latitude,
    try_to_double(payload:Circuit:Location:long::varchar) as longitude
from {{ ref('stg_source_records') }}
where dataset = 'races' and payload:Circuit:circuitId is not null
qualify row_number() over (
    partition by circuit_id
    order by updated_at desc, season desc, round_number desc, business_key
) = 1
