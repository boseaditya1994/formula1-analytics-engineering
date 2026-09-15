{{ config(materialized='table') }}

select
    f.result_key, f.season, f.round_number, r.race_name, f.driver_id, d.driver_code,
    d.given_name || ' ' || d.family_name as driver_name,
    f.constructor_id, c.constructor_name, f.finishing_position, f.grid_position,
    case when f.grid_position > 0 and f.finishing_position > 0
         then f.finishing_position - f.grid_position end as positions_lost,
    case when f.grid_position > 0 and f.finishing_position > 0
         then f.grid_position - f.finishing_position end as positions_gained,
    f.points, f.laps_completed, f.status, f.fastest_lap_rank, f.updated_at
from {{ ref('fct_race_results') }} f
join {{ ref('dim_driver') }} d using (driver_id)
join {{ ref('dim_constructor') }} c using (constructor_id)
join {{ ref('dim_race') }} r using (season, round_number)
