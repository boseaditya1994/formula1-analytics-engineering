select distinct season
from {{ ref('stg_source_records') }}
