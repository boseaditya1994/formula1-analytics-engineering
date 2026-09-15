select result_key
from {{ ref('driver_race_performance') }}
where (grid_position = 0 and (positions_gained is not null or positions_lost is not null))
   or (grid_position > 0 and positions_gained <> grid_position - finishing_position)
