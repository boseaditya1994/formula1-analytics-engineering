with expected as (
    select count(*) as row_count, sum(points) as points
    from {{ ref('fct_race_results') }}
), actual as (
    select count(*) as row_count, sum(points) as points
    from {{ ref('driver_race_performance') }}
)
select expected.row_count as expected_rows, actual.row_count as actual_rows
from expected cross join actual
where expected.row_count <> actual.row_count
   or coalesce(expected.points, 0) <> coalesce(actual.points, 0)
