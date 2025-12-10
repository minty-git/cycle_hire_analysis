{{ config(materialized='view') }}
-- I'd like to set this to a table to prevent the need to import the csvs multiple times, but doing this to reduce size of db

with stg_tfl_cycling_data as (
    select * from {{ ref('stg_tfl_cycling_data') }}
), tfl_station_geocode as (
    select * from {{ ref('tfl_station_geocode') }}
), unioned as (
    
    select

        start_station_name as station_name
        , started_at

    from stg_tfl_cycling_data

    group by all

    union all

    select

        end_station_name as station_name
        , started_at

    from stg_tfl_cycling_data

), final as (
    
    select

        station_name
        , min(started_at) as first_ride_at
        , max(started_at) as last_ride_at
        , count(*) as total_dock_undock_actions

    from unioned

    group by all

)

select

    final.*
    , tfl_station_geocode.station_latitude
    , tfl_station_geocode.station_longitude

from final
left join tfl_station_geocode
    on final.station_name = tfl_station_geocode.station_name
