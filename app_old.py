import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px


# Ideas:
# - A plot that shows the rides (start point, end point, line between) on a map, with a slider that filters on the day
# - Pull in weather data
# - Pull in covid data
# - Pull in NY Geo data that helps to predict the destination. Maybe it predicts travel hubs, or office locations. Maybe it predicts if it's a commute.
# Peak Travel Ratio: Rides_in_Rush_Hour / Total_Rides.
# Weekend Ratio: Rides_on_Weekend / Total_Rides.


# 1. Connect to your DuckDB file
con = duckdb.connect(database=r'C:\Users\minty\Documents\BAMTEC~1\bam_analytics\data\bam_analytics.duckdb')

# Citi Ride Stations per Week
df = con.sql("select ride_week, COUNT(*) as Rides from fact_citi_summary GROUP BY 1").df()
fig = px.bar(df, x='ride_week', y='Rides', title='Citi Rides per Week')
st.plotly_chart(fig, width='stretch', key='citi_rides_per_week')

# Citi Ride Duration per Week
df = con.sql("select ride_week, avg(avg_trip_duration_s/60) as avg_ride_duration_minutes from fact_citi_summary GROUP BY 1").df()
fig = px.bar(df, x='ride_week', y='avg_ride_duration_minutes', title='Citi Ride Duration per Week')
st.plotly_chart(fig, width='stretch', key='citi_ride_duration_per_week')

# New Citi Ride Stations Rides per Week
df = con.sql("select ride_week, count(distinct start_station_name) as stations_started from fact_citi_summary GROUP BY 1").df()
fig = px.bar(df, x='ride_week', y='stations_started', title='New Citi Ride Stations Rides per Week')
st.plotly_chart(fig, width='stretch')

#Citi Rides Over Time by Station Live Year - Bar
df = con.sql("""
    select
        fact_citi_summary.ride_week
        , extract('year' from date(dim_citi_stations.first_ride_at)) as live_year
        ,  COUNT(*) as Rides

    from fact_citi_summary
    inner join dim_citi_stations
        on fact_citi_summary.start_station_name = dim_citi_stations.station_name
    
    GROUP BY ALL
    order by 1,2
"""
).df()
fig = px.bar(df, x='ride_week', y='Rides', title='Citi Rides by Station Live Year per Week', color='live_year', color_continuous_scale='Viridis')
st.plotly_chart(fig, width='stretch', key='citi_rides_by_station_live_year_per_week')

#Citi Rides Over Time by Station Live Year - Line
df = con.sql("""
    select
        fact_citi_summary.ride_week
        , extract('year' from date(dim_citi_stations.first_ride_at)) as live_year
        ,  COUNT(*) as Rides

    from fact_citi_summary
    inner join dim_citi_stations
        on fact_citi_summary.start_station_name = dim_citi_stations.station_name
    
    GROUP BY ALL
    order by 1,2
"""
).df()
df['live_year'] = df['live_year'].astype(str)
fig = px.line(df, x='ride_week', y='Rides', title='Citi Rides Over Time by Station Live Year', color='live_year')
fig.update_traces(mode='lines')
st.plotly_chart(fig, width='stretch')

# Citi Rides Over Time by Rideable Type - Post 2020
df = con.sql("""
    select
        ride_week
        , rideable_type
        ,  COUNT(*) as Rides

    from fact_citi_summary
    GROUP BY ALL
    order by 1,2
"""
).df()
fig = px.line(df, x='ride_week', y='Rides', title='Citi Rides Over Time by Rideable Type - Post 2020', color='rideable_type')
fig.update_traces(mode='lines')
st.plotly_chart(fig, width='stretch')

# Citi Rides Over Time by User Type - Pre 2020
df = con.sql("""
    with agg_all as (
        select
            ride_week
            ,  COUNT(*) as Rides

        from fact_citi_summary
        where ride_week < '2020-01-01'
        GROUP BY ALL
    ), agg_type as (
        select
            ride_week
            , user_type
            ,  COUNT(*) as Rides

        from fact_citi_summary
        where ride_week < '2020-01-01'
        GROUP BY ALL
    )
    select
        agg_all.ride_week
        , agg_type.user_type
        , (agg_type.Rides / agg_all.Rides) * 100 as Percentage

    from agg_all
    left join agg_type
        on agg_all.ride_week = agg_type.ride_week
    order by 1,2 desc
"""
).df()

fig = px.bar(df, x='ride_week', y='Percentage', title='Citi Rides Over Time by User Type - Pre 2020', color='user_type')
st.plotly_chart(fig, width='stretch')

# Citi Rides Over Time by Rideable Type - Post 2020
df = con.sql("""
    with agg_all as (
        select
            ride_week
            ,  COUNT(*) as Rides

        from fact_citi_summary
        where ride_week >= '2020-01-01'
        GROUP BY ALL
    ), agg_type as (
        select
            ride_week
            , rideable_type
            ,  COUNT(*) as Rides

        from fact_citi_summary
        where ride_week >= '2020-01-01'
        GROUP BY ALL
    )
    select
        agg_all.ride_week
        , agg_type.rideable_type
        , (agg_type.Rides / agg_all.Rides) * 100 as Percentage

    from agg_all
    left join agg_type
        on agg_all.ride_week = agg_type.ride_week
    order by 1,2 desc
"""
).df()
fig = px.bar(df, x='ride_week', y='Percentage', title='Citi Rides Over Time by Bike Type - Post 2020', color='rideable_type')
st.plotly_chart(fig, width='stretch')


# # Map Animation
# df = con.sql("""
#     select

#         date_trunc('quarter', started_at) as ride_week
#         , start_station_latitude
#         , start_station_longitude
#         , count(*) as Rides

#     from stg_citibike_trip_data
#     group by all
# """
# ).df()
# df['ride_week'] = df['ride_week'].astype(str) # Crucial for animation

# # Set the initial view centered on NYC
# center_lat = 40.730610
# center_lon = -73.935242

# fig = px.scatter_map(
#     df,
#     lat="start_station_latitude",
#     lon="start_station_longitude",
#     size="Rides",
#     color="Rides",
#     animation_frame="ride_week",
    
#     # Map Configuration
#     zoom=10, 
#     height=600,
#     center=dict(lat=center_lat, lon=center_lon),
#     map_style="carto-positron", # A clean, light map style
#     color_continuous_scale=px.colors.sequential.Viridis,
#     title="NYC Citi Bike Hotspot Evolution"
# )

# # Optional: Adjust marker opacity and size limits for better visualization
# fig.update_layout(
#     sliders=[dict(
#         active=0,
#         currentvalue={"prefix": "Week: "},
#         pad={"t": 20}
#     )],
#     margin={"r":0,"t":40,"l":0,"b":0}
# )
# fig.update_traces(marker=dict(opacity=0.7, sizemin=3, sizemode='area'))

# st.plotly_chart(fig, width='stretch', key='hotspot_animation')


# Map Per Year
df_maps = con.sql("""
    SELECT
        EXTRACT(YEAR FROM started_at) AS ride_year,
        ROUND(start_station_longitude, 0) AS start_lng,
        ROUND(start_station_latitude, 0) AS start_lat,
        COUNT(*) AS Rides
    FROM stg_citibike_trip_data
    GROUP BY ALL
    HAVING ride_year IS NOT NULL
    ORDER BY 1, 4 DESC
"""
).df()

# CRITICAL: Convert the numeric 'ride_year' to a string for faceting.
# This ensures each year gets its own discrete column/map.
df_maps['ride_year'] = df_maps['ride_year'].astype(str)

# --- Define Center Coordinates for NYC ---
center_lat = 40.730610
center_lon = -73.935242

mapbox_config = dict(
    zoom=9.5, 
    height=400, # Reduce height for the grid
    center=dict(lat=center_lat, lon=center_lon),
    mapbox_style="carto-positron",
    color_continuous_scale=px.colors.sequential.Plasma,
)

# Get the list of unique years and sort them
years = sorted(df_maps['ride_year'].unique())

# Create 3 columns at a time (for the 2x3 grid)
cols = st.columns(3)
col_index = 0

for year in years:
    # Filter the data for the current year
    df_year = df_maps[df_maps['ride_year'] == year]
    
    # Create the density map for the single year
    fig = px.density_mapbox(
        df_year,
        lat="start_lat",
        lon="start_lng",
        z="Rides",
        radius=10, 
        title=f"Year: {int(year)}", # Use title to label the year
        **mapbox_config # Pass common map configs
    )

    # Place the figure into the current column
    with cols[col_index]:
        # Use a unique key for the Streamlit element
        st.plotly_chart(fig, use_container_width=True, key=f'density_map_{year}')
    
    # Move to the next column (or wrap around to the next row)
    col_index = (col_index + 1) % 3

    # If we just finished a row (col_index == 0 after increment), start a new set of columns
    # We only need to start a new row after the first 3 elements (years)
    if col_index == 0 and years.index(year) < len(years) - 1:
        cols = st.columns(3)