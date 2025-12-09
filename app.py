import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from datetime import date

# Ideas:
# - A plot that shows the rides (start point, end point, line between) on a map, with a slider that filters on the day
# - Pull in weather data
# - Pull in covid data
# - Pull in NY Geo data that helps to predict the destination. Maybe it predicts travel hubs, or office locations. Maybe it predicts if it's a commute.

con = duckdb.connect(database='cycle_hire_analysis.duckdb')


PRESET_START_DATE = date(2020, 3, 14)
PRESET_END_DATE = date(2021, 5, 21)
MIN_DATA_DATE = date(2018, 1, 1)
MAX_DATA_DATE = date(2023, 11, 30)

if 'date_slider' not in st.session_state:
    # Initialize the slider to the full range
    st.session_state.date_slider = (MIN_DATA_DATE, MAX_DATA_DATE)

def update_slider_dates():
    """Updates the slider's value (st.session_state.date_slider) based on the checkbox."""
    if st.session_state.preset_checked:
        # Checkbox is Ticked: Update the single 'date_slider' key to the preset dates
        st.session_state.date_slider = (PRESET_START_DATE, PRESET_END_DATE)
    else:
        # Checkbox is UNTicked: Revert the 'date_slider' key to the full range
        st.session_state.date_slider = (MIN_DATA_DATE, MAX_DATA_DATE)

# --- 4. Place Checkbox and Slider in App (Fixed) ---

st.header("Date Filter Controls")

# Create the Slider
slider_min, slider_max = st.slider(
    "Select Date Range",
    min_value=MIN_DATA_DATE,
    max_value=MAX_DATA_DATE,
    format="MMM YYYY",
    key='date_slider'
)

# Create the Tickbox
st.checkbox(
    "Filter to COVID-19 Impact Period (Mar 2020 - May 2021)",
    key='preset_checked',
    on_change=update_slider_dates
)


citi_tab, tfl_tab, both_tab = st.tabs(["New York", "London", "Comparison"])

with citi_tab:
    st.image('https://images.ctfassets.net/p6ae3zqfb1e3/1rbjR48QnBe6cL8Ti6tPmV/08f9e1a62a6ef6ec1cddc4bc5a12f8d1/imageedit_2_9337177880.png?w=1500&q=60&fm=', width=1500)

    # Citi Rides Over Time by Station Live Year - Bar
    # Map Animation
    df = con.execute("""
        select
            ride_week
            , station_latitude as start_station_latitude
            , station_longitude as start_station_longitude
            , sum(rides) as Rides

        from citi_statistics_by_week
        where ride_week between ? and ?
        group by all
        order by ride_week
    """
    , [slider_min, slider_max]).df()
    df['ride_week'] = df['ride_week'].astype(str) # Crucial for animation

    # Set the initial view centered on NYC
    center_lat = 40.750610
    center_lon = -73.935242

    # 💡 FIX 1: Use px.scatter_mapbox (the function for Mapbox tile maps)
    fig = px.scatter_mapbox(
        df,
        lat="start_station_latitude",
        lon="start_station_longitude",
        size="Rides",
        color="Rides",
        animation_frame="ride_week",
        
        # Map Configuration
        zoom=10, 
        height=600,
        center=dict(lat=center_lat, lon=center_lon),
        # 💡 FIX 2: Use mapbox_style (the correct argument for setting the background tile)
        mapbox_style="carto-positron", 
        color_continuous_scale=px.colors.sequential.Viridis,
        title="NYC Citi Bike Hotspot Evolution"
    )

    fig.update_layout(
        sliders=[],
        margin={"r":0,"t":40,"l":0,"b":0} # Keep your margins
    )

    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        
        sliders=[dict(
            active=0,
            currentvalue={"prefix": "Week: "},
            pad={"t": 20},
            # Key: Ensure the slider's transition speed matches the buttons
            transition={"duration": 100, "easing": "linear"}
        )],
        
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                x=0.03, # Position the buttons near the left edge
                y=0.05, # Position them slightly above the slider/margin
                buttons=[
                    # FAST PLAY BUTTON
                    dict(
                        label="▶️ Play",
                        method="animate",
                        args=[
                            None, 
                            {
                                "frame": {"duration": 100, "redraw": True}, # 100ms per frame
                                "fromcurrent": True, 
                                "transition": {"duration": 50, "easing": "linear"}
                            }
                        ]
                    ),
                    # STOP BUTTON
                    dict(
                        label="⏸️ Stop",
                        method="animate",
                        args=[
                            [None], # Pauses the animation at the current frame
                            {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}
                        ]
                    )
                ]
            )
        ]
    )

    st.plotly_chart(fig, width='stretch')

    # Citi Ride Stations per Week
    df = con.execute("select ride_week, sum(rides) as Rides from citi_statistics_by_week where ride_week between ? and ? group by all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Rides', title='Weekly Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    # Citi Ride Duration per Week
    df = con.execute("select ride_week, round(sum(ride_duration_minutes)/sum(rides), 2) as avg_ride_duration_minutes from citi_statistics_by_week where ride_week between ? and ? GROUP BY all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='avg_ride_duration_minutes', title='Ride Duration - Minutes')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    # Citi Stations per Week
    df = con.execute("select ride_week, count(distinct start_station_name) as stations_started from citi_statistics_by_week where ride_week between ? and ? GROUP BY all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='stations_started', title='Active Stations')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    # Citi Rides Over Time by Station Live Year - Bar
    df = con.execute("select ride_week, station_live_year, sum(rides) as Rides from citi_statistics_by_week where ride_week between ? and ? GROUP BY all order by 1,2", [slider_min, slider_max]).df()
    df['station_live_year'] = df['station_live_year'].astype(str)
    fig = px.bar(df, x='ride_week', y='Rides', title='Active Stations by Live Year', color='station_live_year', color_continuous_scale='Viridis')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    # Citi Rides Over Time by Station Live Year - Bar
    df = con.execute("""
        with agg_all as (
            select
                ride_week
                , sum(rides) as Rides
            from citi_statistics_by_week
            GROUP BY all
        ), agg_type as (
            select
                ride_week
                , sum(rides) as Rides
            from citi_statistics_by_week
            where is_ride_weekend
            GROUP BY all
        )
        select
            agg_all.ride_week
            , (agg_type.Rides / agg_all.Rides) * 100 as Percentage
        from agg_all
        inner join agg_type
            on agg_all.ride_week = agg_type.ride_week
        where agg_all.ride_week between ? and ?
        order by 1,2
    """, [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Percentage', title='Percentage of Weekend Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')


    # Citi Rides Over Time by Station Live Year - Bar
    df = con.execute("""
        with agg_all as (
            select
                ride_week
                , sum(rides) as Rides
            from citi_statistics_by_week
            GROUP BY all
        ), agg_type as (
            select
                ride_week
                , sum(rides) as Rides
            from citi_statistics_by_week
            where is_ride_rush_hour
            GROUP BY all
        )
        select
            agg_all.ride_week
            , (agg_type.Rides / agg_all.Rides) * 100 as Percentage
        from agg_all
        inner join agg_type
            on agg_all.ride_week = agg_type.ride_week
        where agg_all.ride_week between ? and ?
        order by 1,2
    """, [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Percentage', title='Percentage of Rush Hour Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

with tfl_tab:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image('https://play-lh.googleusercontent.com/Ri24WZyAocyMtFxscTxCir219rx--utI8MmJ-oKhxd7s5304G67E_WLzWh5xdjqYl4Q', width=256)

    #
    df = con.execute("select ride_week, sum(rides) as Rides from tfl_statistics_by_week where ride_week between ? and ? group by all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Rides', title='Weekly Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    #
    df = con.execute("select ride_week, round(sum(ride_duration_minutes)/sum(rides), 2) as avg_ride_duration_minutes from tfl_statistics_by_week where ride_week between ? and ? GROUP BY all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='avg_ride_duration_minutes', title='Ride Duration - Minutes')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    #
    df = con.execute("select ride_week, count(distinct start_station_name) as stations_started from tfl_statistics_by_week where ride_week between ? and ? GROUP BY all order by ride_week", [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='stations_started', title='Active Stations')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    #
    df = con.execute("select ride_week, station_live_year, sum(rides) as Rides from tfl_statistics_by_week where ride_week between ? and ? GROUP BY all order by 1,2", [slider_min, slider_max]).df()
    df['station_live_year'] = df['station_live_year'].astype(str)
    fig = px.bar(df, x='ride_week', y='Rides', title='Active Stations by Live Year', color='station_live_year', color_continuous_scale='Viridis')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    #
    df = con.execute("""
        with agg_all as (
            select
                ride_week
                , sum(rides) as Rides
            from tfl_statistics_by_week
            GROUP BY all
        ), agg_type as (
            select
                ride_week
                , sum(rides) as Rides
            from tfl_statistics_by_week
            where is_ride_weekend
            GROUP BY all
        )
        select
            agg_all.ride_week
            , (agg_type.Rides / agg_all.Rides) * 100 as Percentage
        from agg_all
        inner join agg_type
            on agg_all.ride_week = agg_type.ride_week
        where agg_all.ride_week between ? and ?
        order by 1,2
    """, [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Percentage', title='Percentage of Weekend Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

    #
    df = con.execute("""
        with agg_all as (
            select
                ride_week
                , sum(rides) as Rides
            from tfl_statistics_by_week
            GROUP BY all
        ), agg_type as (
            select
                ride_week
                , sum(rides) as Rides
            from tfl_statistics_by_week
            where is_ride_rush_hour
            GROUP BY all
        )
        select
            agg_all.ride_week
            , (agg_type.Rides / agg_all.Rides) * 100 as Percentage
        from agg_all
        inner join agg_type
            on agg_all.ride_week = agg_type.ride_week
        where agg_all.ride_week between ? and ?
        order by 1,2
    """, [slider_min, slider_max]).df()
    fig = px.line(df, x='ride_week', y='Percentage', title='Percentage of Rush Hour Rides')
    if slider_min <= PRESET_START_DATE <= slider_max:
        fig.add_vline(x=PRESET_START_DATE, line_width=3, line_dash="dash", line_color="green")
    if slider_min <= PRESET_END_DATE <= slider_max:
        fig.add_vline(x=PRESET_END_DATE, line_width=3, line_dash="dash", line_color="green")
    st.plotly_chart(fig, width='stretch')

with both_tab:
    citi_col, tfl_col = st.columns(2)

    with citi_col:
        df = con.execute("select sum(rides) as rides from citi_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Total Rides - New York", value=f"{df['rides'].iloc[0]:,}")

        df = con.execute("select count(distinct start_station_name) as stations from citi_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Active Stations - New York", value=f"{df['stations'].iloc[0]:,}")

        df = con.execute("select round((count(case when is_ride_weekend then 1 end) / count(*) * 100), 2) as perc_weekend from citi_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Percentage of Rides on Weekend - New York", value=f"{df['perc_weekend'].iloc[0]:,}")

    with tfl_col:
        df = con.execute("select sum(rides) as rides from tfl_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Total Rides - London", value=f"{df['rides'].iloc[0]:,}")

        df = con.execute("select count(distinct start_station_name) as stations from tfl_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Active Stations - London", value=f"{df['stations'].iloc[0]:,}")

        df = con.execute("select round((count(case when is_ride_weekend then 1 end) / count(*) * 100), 2) as perc_weekend from tfl_statistics_by_week where ride_week between ? and ?", [slider_min, slider_max]).df()
        st.metric(label="Percentage of Rides on Weekend - London", value=f"{df['perc_weekend'].iloc[0]:,}")
