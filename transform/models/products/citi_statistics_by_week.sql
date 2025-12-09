{{ config(materialized='table') }}

with rides as (
    select * from {{ ref('fact_citi_rides') }}
), stations as (
    select * from {{ ref('dim_citi_stations') }}
), station_statistics as (
    select * from {{ ref('trf_citi_station_statistics_by_week') }}
), final as (

    select

        date_trunc('week', rides.started_at) as ride_week
        , if(extract('dayofweek' from rides.started_at) in (0, 6), true, false) as is_ride_weekend
        , if(extract('hour' from rides.started_at) in (6,7,8,9,16,17,18,19), true, false) as is_ride_rush_hour
        , rides.start_station_name
        , extract('year' from date(start_stations.first_ride_at)) as station_live_year
        , start_stations.station_latitude
        , start_stations.station_longitude
        , COUNT(*) as rides
        , sum(rides.trip_duration_s)/60 as ride_duration_minutes

    from rides
    inner join stations as start_stations
        on start_stations.station_name = rides.start_station_name

    group by all

)

select

    final.*
    , station_statistics.station_dock_actions
    , station_statistics.station_undock_actions

from final
inner join station_statistics
    on station_statistics.station_name = final.start_station_name
        and station_statistics.ride_week = final.ride_week
