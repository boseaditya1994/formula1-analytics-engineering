{{ config(materialized='view') }}

select
    dataset,
    business_key,
    season::integer as season,
    round_number::integer as round_number,
    payload,
    payload_hash,
    first_ingested_at,
    updated_at,
    run_id
from {{ source('raw', 'source_records') }}
