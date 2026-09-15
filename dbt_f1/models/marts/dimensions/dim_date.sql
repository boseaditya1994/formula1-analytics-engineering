with offsets as (
    select row_number() over (order by seq4()) - 1 as day_offset
    from table(generator(rowcount => 366))
), dates as (
    select dateadd(day, day_offset, date_from_parts(season, 1, 1))::date as date_day,
           season
    from {{ ref('dim_season') }} cross join offsets
)
select date_day, season as year, month(date_day) as month_number,
       quarter(date_day) as quarter_number, dayofweekiso(date_day) as iso_day_of_week
from dates
where year(date_day) = season
