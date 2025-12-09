{{ config(materialized='view') }}

with source as (
    select * from {{ source('csvs', 'tfl_cycling_data') }}
), final as (

    select

        filename
        , try_strptime("Start Date", ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']) as started_at
        , try_strptime("End Date", ['%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M']) as ended_at
        , coalesce(cast("Start station number" as VARCHAR), cast("Start station number" as VARCHAR)) as start_station_id
        , coalesce(cast("End station number" as VARCHAR), cast("EndStation Id" as VARCHAR)) as end_station_id
        , coalesce("StartStation Name", "Start station") as start_station_name
        , coalesce("EndStation Name", "End station") as end_station_name
        , coalesce(cast("Duration" as BIGINT), epoch("Total duration"::INTERVAL)) as trip_duration_s
        , coalesce("Bike Id", cast("Bike number" as BIGINT)) as bike_id 
        , "Total duration (ms)" as trip_duration_ms -- not in early data
        , "Bike model" as bike_model -- not in early data
        , Number as number -- not in early data

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
