{{ config(materialized='view') }}
-- I'd like to set this to a table to prevent the need to import the csvs multiple times, but doing this to reduce size of db

with fact_tfl_rides as (
    select * from {{ ref('fact_tfl_rides') }}
), unioned as (
    
    select

        start_station_name as station_name
        , started_at
        , true as is_dock

    from fact_tfl_rides

    group by all

    union all

    select

        end_station_name as station_name
        , started_at
        , false as is_dock

    from fact_tfl_rides

), final as (
    
    select

        date_trunc('week', started_at) as ride_week
        , station_name
        , count(case when is_dock then station_name end) as station_dock_actions
        , count(case when not is_dock then station_name end) as station_undock_actions

    from unioned

    group by all

)

select * from final
