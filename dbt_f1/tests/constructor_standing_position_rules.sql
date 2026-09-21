select standing_key
from {{ ref('fct_constructor_standings') }}
where championship_position_text is null
   or (championship_position is null and championship_position_text <> '-')
   or (championship_position is not null and
       (championship_position < 1 or championship_position_text = '-'))
