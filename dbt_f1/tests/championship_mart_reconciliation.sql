with comparisons as (
    select s.standing_key as source_key, m.standing_key as mart_key,
           s.championship_points as source_points, m.championship_points as mart_points
    from {{ ref('fct_driver_standings') }} s
    full outer join {{ ref('driver_championship_progression') }} m using (standing_key)
    union all
    select s.standing_key, m.standing_key, s.championship_points, m.championship_points
    from {{ ref('fct_constructor_standings') }} s
    full outer join {{ ref('constructor_championship_progression') }} m using (standing_key)
)
select * from comparisons
where source_key is null or mart_key is null or source_points <> mart_points
