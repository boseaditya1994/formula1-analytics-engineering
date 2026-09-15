{{ config(materialized='table') }}

select
    payload:record:Constructor:constructorId::varchar as constructor_id,
    payload:record:Constructor:name::varchar as constructor_name,
    payload:record:Constructor:nationality::varchar as nationality
from {{ ref('stg_source_records') }}
where dataset in ('results', 'qualifying', 'sprint', 'constructorstandings')
  and payload:record:Constructor:constructorId is not null
qualify row_number() over (
    partition by constructor_id
    order by updated_at desc, season desc, round_number desc, dataset, business_key
) = 1
