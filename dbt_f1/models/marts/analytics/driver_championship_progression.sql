select
    s.*,
    d.given_name || ' ' || d.family_name as driver_name,
    r.race_name,
    s.championship_points - lag(s.championship_points) over (
        partition by s.season, s.driver_id order by s.round_number
    ) as points_change,
    lag(s.championship_position) over (
        partition by s.season, s.driver_id order by s.round_number
    ) - s.championship_position as championship_positions_gained
from {{ ref('fct_driver_standings') }} s
join {{ ref('dim_driver') }} d using (driver_id)
join {{ ref('dim_race') }} r using (race_key)
