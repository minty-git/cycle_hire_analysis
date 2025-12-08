{{ config(materialized='view') }}
-- I'd like to set this to a table to prevent the need to import the csvs multiple times, but doing this to reduce size of db

with stg_tfl_cycling_data as (
    select * from {{ ref('stg_tfl_cycling_data') }}
), final as (
    
    select * from stg_tfl_cycling_data

)

select * from final
