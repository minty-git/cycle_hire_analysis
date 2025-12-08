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
# con = duckdb.connect(database=r'C:\Users\minty\OneDrive\Documents\git\cycle_hire_analysis\cycle_hire_analysis.duckdb')
con = duckdb.connect(database='cycle_hire_analysis.duckdb')

# Citi Ride Stations per Week
df = con.sql("select ride_week, sum(rides) as Rides from citi_statistics_by_week group by all").df()
fig = px.bar(df, x='ride_week', y='Rides', title='Citi Rides per Week')
st.plotly_chart(fig, width='stretch', key='citi_rides_per_week')

# Citi Ride Duration per Week
df = con.sql("select ride_week, round(sum(ride_duration_minutes)/sum(rides), 2) as avg_ride_duration_minutes from citi_statistics_by_week GROUP BY all").df()
fig = px.bar(df, x='ride_week', y='avg_ride_duration_minutes', title='Citi Ride Duration per Week')
st.plotly_chart(fig, width='stretch', key='citi_ride_duration_per_week')

# Citi Stations per Week
df = con.sql("select ride_week, stations_started from citi_statistics_by_week GROUP BY all").df()
fig = px.bar(df, x='ride_week', y='stations_started', title='Citi Stations per Week')
st.plotly_chart(fig, width='stretch')

# Citi Rides Over Time by Station Live Year - Bar
df = con.sql("select ride_week, station_live_year, sum(rides) as Rides from citi_statistics_by_week GROUP BY all order by 1,2").df()
df['station_live_year'] = df['station_live_year'].astype(str)
fig = px.bar(df, x='ride_week', y='Rides', title='Citi Rides by Station Live Year per Week', color='station_live_year', color_continuous_scale='Viridis')
st.plotly_chart(fig, width='stretch', key='citi_rides_by_station_live_year_per_week')
