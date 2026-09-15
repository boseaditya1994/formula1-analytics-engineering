select result_key
from {{ ref('fct_race_results') }}
where points < 0 or finishing_position < 0 or grid_position < 0
