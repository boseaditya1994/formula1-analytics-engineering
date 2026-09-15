with source_counts as (
    select dataset, count(*) as row_count
    from {{ ref('stg_source_records') }}
    where dataset in ('results', 'qualifying', 'sprint', 'driverstandings', 'constructorstandings')
    group by dataset
), fact_counts as (
    select 'results' as dataset, count(*) as row_count from {{ ref('fct_race_results') }}
    union all
    select 'qualifying', count(*) from {{ ref('fct_qualifying_results') }}
    union all
    select 'sprint', count(*) from {{ ref('fct_sprint_results') }}
    union all
    select 'driverstandings', count(*) from {{ ref('fct_driver_standings') }}
    union all
    select 'constructorstandings', count(*) from {{ ref('fct_constructor_standings') }}
)
select f.dataset, s.row_count as source_count, f.row_count as fact_count
from fact_counts f left join source_counts s using (dataset)
where f.row_count <> coalesce(s.row_count, 0)
