{{ config(materialized='view') }}

with source as (
    select * from {{ source('csvs', 'citibike_trip_data') }}
), final as (
    
    select

        filename
        , coalesce(starttime, started_at) as started_at
        , coalesce(stoptime, ended_at) as ended_at
        , nullif(coalesce("start station id", start_station_id),'NULL') as start_station_id -- some station_id 119 vs 119.0
        , nullif(coalesce("end station id", end_station_id), 'NULL') as end_station_id -- some station_id 119 vs 119.0
        , coalesce("start station name", start_station_name) as start_station_name
        , coalesce("end station name", end_station_name) as end_station_name
        , coalesce("start station latitude", start_lat) as start_station_latitude
        , coalesce("end station latitude", end_lat) as end_station_latitude
        , coalesce("start station longitude", start_lng) as start_station_longitude
        , coalesce("end station longitude", end_lng) as end_station_longitude
        , tripduration as trip_duration_s -- not in late data
        , bikeid as bike_id -- not in late data
        , usertype as user_type -- not in late data -- (Customer = 24-hour pass or 3-day pass user; Subscriber = Annual Member)
        , "birth year" as birth_year -- not in late data
        , case
            when gender = 0 then null
            when gender = 1 then 'Male'
            when gender = 2 then 'Female'
        end as gender
        , gender -- not in late data
        , ride_id -- not in early data
        , rideable_type -- not in early data
        , member_casual -- not in early data

    from source

)

select

    * exclude(trip_duration_s, start_station_name, end_station_name)
    , case
        when trip_duration_s is null then date_diff('second', started_at, ended_at)
        else trip_duration_s
    end as trip_duration_s
    , nullif(replace(replace(replace(start_station_name, '\t&', ''), 't\t', ' '), '\t', ' '), 'NULL') as start_station_name
    , nullif(replace(replace(replace(end_station_name, '\t&', ''), 't\t', ' '), '\t', ' '), 'NULL') as end_station_name

from final
where started_at >= '2018-01-01'
    and started_at <= '2023-11-30'
