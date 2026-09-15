{{ config(materialized='table') }}

select
    payload:record:Driver:driverId::varchar as driver_id,
    payload:record:Driver:code::varchar as driver_code,
    payload:record:Driver:givenName::varchar as given_name,
    payload:record:Driver:familyName::varchar as family_name
from {{ ref('stg_source_records') }}
where dataset in ('results', 'qualifying', 'sprint', 'driverstandings')
  and payload:record:Driver:driverId is not null
qualify row_number() over (
    partition by driver_id
    order by updated_at desc, season desc, round_number desc, dataset, business_key
) = 1
