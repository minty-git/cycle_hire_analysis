{{ config(materialized='view') }}
-- I'd like to set this to a table to prevent the need to import the csvs multiple times, but doing this to reduce size of db

with stg_citibike_trip_data as (
    select * from {{ ref('stg_citibike_trip_data') }}
), unioned as (
    
    select

        -- start_station_id as station_id
        start_station_name as station_name
        , start_station_latitude as station_latitude
        , start_station_longitude as station_longitude
        , started_at

    from stg_citibike_trip_data

    group by all

    union all

    select

        -- end_station_id as station_id
        end_station_name as station_name
        , end_station_latitude as station_latitude
        , end_station_longitude as station_longitude
        , started_at

    from stg_citibike_trip_data

), final as (
    
    select

        station_name
        , min(started_at) as first_ride_at
        , max(started_at) as last_ride_at
        , median(station_latitude) as station_latitude
        , median(station_longitude) as station_longitude
        , count(*) as total_dock_undock_actions

    from unioned

    group by all

)

select * from final
