select season, round_number, driver_id, count(*) as row_count
from {{ ref('fct_race_results') }}
group by season, round_number, driver_id
having count(*) > 1
