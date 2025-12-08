{{ config(materialized='table') }}

with rides as (
    select * from {{ ref('fact_tfl_rides') }}
), stations as (
    select * from {{ ref('dim_tfl_stations') }}
), final as (

    select

         date_trunc('week', rides.started_at) as ride_week
        , extract('year' from date(start_stations.first_ride_at)) as station_live_year
        , COUNT(*) as rides
        , sum(rides.trip_duration_s)/60 as ride_duration_minutes
        , count(distinct rides.start_station_name) as stations_started

    from rides
    inner join stations as start_stations
        on start_stations.station_name = rides.start_station_name

    group by all

)

select * from final