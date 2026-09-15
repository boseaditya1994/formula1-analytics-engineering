select dataset, business_key, count(*) as row_count
from {{ ref('stg_source_records') }}
group by dataset, business_key
having count(*) > 1
