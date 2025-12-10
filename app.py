import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from datetime import date

# --- Page Configuration ---
st.set_page_config(page_title="NYC vs London Cycle Analysis", layout="wide")

# --- Database Connection ---
@st.cache_resource
def get_connection():
    try:
        return duckdb.connect(database='cycle_hire_analysis.duckdb')
    except:
        st.error("Could not connect to database.")
        return None

con = get_connection()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page:", ["📊 Comparison", "🗽 New York Deep Dive", "🇬🇧 London Deep Dive"])
    
    st.markdown("---")
    st.header("Global Filters")
    
    # Constants
    MIN_DATA_DATE = date(2018, 1, 1)
    MAX_DATA_DATE = date(2023, 11, 30)
    PRESET_START = date(2020, 3, 1)
    PRESET_END = date(2021, 6, 1)

    # Session State for Slider
    if 'date_slider' not in st.session_state:
        st.session_state.date_slider = (MIN_DATA_DATE, MAX_DATA_DATE)

    def set_covid_range():
        if st.session_state.covid_toggle:
            st.session_state.date_slider = (PRESET_START, PRESET_END)
        else:
            st.session_state.date_slider = (MIN_DATA_DATE, MAX_DATA_DATE)

    st.toggle("Focus on Pandemic Era", key='covid_toggle', on_change=set_covid_range)

    slider_min, slider_max = st.slider(
        "Date Range",
        min_value=MIN_DATA_DATE,
        max_value=MAX_DATA_DATE,
        key='date_slider',
        format="MMM YYYY"
    )
    
    st.caption(f"Showing: {slider_min.strftime('%b %Y')} - {slider_max.strftime('%b %Y')}")



# ==============================================================================
# PAGE 1: HEAD-TO-HEAD COMPARISON (The Version You Liked)
# ==============================================================================
if page == "📊 Comparison":
    def get_city_weekly_data(table_name, start_date, end_date):
        query = f"""
            SELECT 
                ride_week,
                SUM(rides) as total_rides,
                SUM(ride_duration_minutes) as total_duration,
                COUNT(DISTINCT start_station_name) as active_stations,
                SUM(CASE WHEN is_ride_rush_hour AND NOT is_ride_weekend THEN rides ELSE 0 END) as rush_hour_rides,
                SUM(CASE WHEN is_ride_weekend THEN rides ELSE 0 END) as weekend_rides
            FROM {table_name}
            WHERE ride_week BETWEEN ? AND ?
            GROUP BY 1
            ORDER BY 1
        """
        df = con.execute(query, [start_date, end_date]).df()
        
        # Feature Engineering
        df['avg_duration'] = df['total_duration'] / df['total_rides']
        df['rush_hour_pct'] = (df['rush_hour_rides'] / df['total_rides']) * 100
        df['weekend_pct'] = (df['weekend_rides'] / df['total_rides']) * 100
        return df

    # Load Data
    df_nyc = get_city_weekly_data('citi_statistics_by_week', slider_min, slider_max)
    df_ldn = get_city_weekly_data('tfl_statistics_by_week', slider_min, slider_max)

    # Add 'City' label for merging
    df_nyc['City'] = 'New York (Citi Bike)'
    df_ldn['City'] = 'London (TfL)'
    df_combined = pd.concat([df_nyc, df_ldn])


    # --- SECTION 1: THE SCALE ---
    st.header("1. Scale & Growth: The New York Giant")
    st.write(
        """
        First, let's look at the sheer volume. While both systems are vital to their cities, **New York operates on a different scale**.
        Since 2018, NYC has aggressively expanded its network, fueling a massive divergence in ridership numbers compared to London.
        """
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NYC Total Rides", f"{df_nyc['total_rides'].sum():,.0f}")
    col2.metric("NYC Peak Active Stations", f"{df_nyc['active_stations'].max():,.0f}")
    col3.metric("LDN Total Rides", f"{df_ldn['total_rides'].sum():,.0f}")
    col4.metric("LDN Peak Active Stations", f"{df_ldn['active_stations'].max():,.0f}")

    # Chart: Total Rides Over Time
    fig_vol = px.line(
        df_combined, 
        x='ride_week', 
        y='total_rides', 
        color='City',
        title='Weekly Ridership Volume (2018-2023)',
        labels={'ride_week': 'Date', 'total_rides': 'Weekly Rides'},
        color_discrete_map={'New York (Citi Bike)': '#003399', 'London (TfL)': '#DC241f'} # Official brand colors
    )
    st.plotly_chart(fig_vol, use_container_width=True)


    # --- SECTION 2: THE COVID PIVOT ---
    st.header("2. The COVID Pivot: From Commuting to Joyriding")
    st.markdown(
        """
        The pandemic fundamentally broke the "Commuter" model. In 2020, as offices closed, bikes transformed from 
        **"Last Mile Transport"** into **"Mobile Gyms."**
        """
    )

    tab_habit1, tab_habit2, tab_habit3 = st.tabs(["📉 The Death of Rush Hour", "⏱️ The Joyride Spike", "🏗️ Network Expansion"])

    with tab_habit1:
        st.caption("How much of the total traffic happens during traditional rush hours (6-9am, 4-7pm)?")
        fig_rush = px.line(
            df_combined, 
            x='ride_week', 
            y='rush_hour_pct', 
            color='City',
            title='Percentage of Rides During Rush Hour',
            labels={'rush_hour_pct': '% of Rides in Rush Hour'},
            color_discrete_map={'New York (Citi Bike)': '#003399', 'London (TfL)': '#DC241f'}
        )
        # Add annotation for lockdown
        fig_rush.add_vrect(x0="2020-03-20", x1="2021-01-01", fillcolor="gray", opacity=0.1, annotation_text="Lockdowns", annotation_position="top left")
        st.plotly_chart(fig_rush, use_container_width=True)
        st.info("**Insight:** Notice the plunge in early 2020. London dropped from ~57% commuter traffic to <45%. NYC saw a similar collapse. Even in 2023, rush hour peaks haven't fully recovered to 2019 levels, reflecting the **Hybrid Work** era.")

    with tab_habit2:
        st.caption("How long is the average trip?")
        fig_dur = px.line(
            df_combined, 
            x='ride_week', 
            y='avg_duration', 
            color='City',
            title='Average Trip Duration (Minutes)',
            labels={'avg_duration': 'Avg Duration (min)'},
            color_discrete_map={'New York (Citi Bike)': '#003399', 'London (TfL)': '#DC241f'}
        )
        fig_dur.add_vrect(x0="2020-03-20", x1="2021-01-01", fillcolor="gray", opacity=0.1, annotation_text="Lockdowns", annotation_position="top left")
        st.plotly_chart(fig_dur, use_container_width=True)
        st.info("**Insight:** In 2020, average trip times in NYC nearly **doubled** (from ~14m to ~25m). With gyms closed, New Yorkers used Citi Bikes for long leisure rides. London saw a similar, though less extreme, effect.")

    with tab_habit3:
        st.caption("How has the physical network grown?")
        fig_stations = px.line(
            df_combined, 
            x='ride_week', 
            y='active_stations', 
            color='City',
            title='Active Stations Over Time',
            color_discrete_map={'New York (Citi Bike)': '#003399', 'London (TfL)': '#DC241f'}
        )
        fig_stations.add_vrect(x0="2020-03-20", x1="2021-01-01", fillcolor="gray", opacity=0.1, annotation_text="Lockdowns", annotation_position="top left")
        st.plotly_chart(fig_stations, use_container_width=True)
        st.info("**Insight:** NYC's growth is relentless. They continued to install hundreds of stations through the pandemic, whereas London's network footprint has remained relatively stable.")


    # --- SECTION 3: SEASONALITY ---
    st.header("3. Battling the Elements: The Seasonal Pulse")
    st.write("Finally, we must account for the weather. New York's continental climate creates **extreme seasonality** compared to London's temperate (albeit rainy) maritime climate.")

    # Prepare Seasonality Data (Year-Over-Year Overlay)
    def get_seasonality_data(table_name):
        return con.execute(f"""
            SELECT 
                EXTRACT(MONTH FROM date(ride_week)) as month_num,
                EXTRACT(YEAR FROM date(ride_week))::STRING as year,
                SUM(rides) as total_rides
            FROM {table_name}
            WHERE ride_week >= '2019-01-01'
            GROUP BY 1, 2
            ORDER BY 1
        """).df()

    df_seas_nyc = get_seasonality_data('citi_statistics_by_week')
    df_seas_ldn = get_seasonality_data('tfl_statistics_by_week')

    col_seas1, col_seas2 = st.columns(2)

    with col_seas1:
        st.subheader("New York Seasonality")
        fig_seas_ny = px.line(
            df_seas_nyc, x='month_num', y='total_rides', color='year',
            title='NYC: Monthly Rides by Year',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        st.plotly_chart(fig_seas_ny, use_container_width=True)

    with col_seas2:
        st.subheader("London Seasonality")
        fig_seas_ldn = px.line(
            df_seas_ldn, x='month_num', y='total_rides', color='year',
            title='London: Monthly Rides by Year',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        st.plotly_chart(fig_seas_ldn, use_container_width=True)

    st.success(
        """
        **Key Takeaway:** * **NYC** ridership crashes in winter (Jan rides are often 30-40% of July peaks).
        * **London** is much flatter. The "dip" in winter is far less severe, meaning London relies less on fair weather than NYC does.
        * **2023 Growth:** Notice how the 2023 line (likely the top line) in NYC towers above previous years, showing that the system's growth is outpacing its seasonality.
        """
    )

# ==============================================================================
# PAGE 2: NEW YORK DEEP DIVE
# ==============================================================================
elif page == "🗽 New York Deep Dive":
    st.title("🗽 New York: The Mobile Gym")
    st.write("Beyond the commute, NYC reveals a fascinating story of behavioral shifts. When gyms closed in 2020, the bike network took over.")

    # 1. THE MAP ANIMATION
    st.subheader("📍 Hotspot Evolution")
    st.write("Visualize how ridership clusters shift over time across the city.")

    df_map = con.execute("""
        SELECT 
            ride_week,
            station_latitude as lat,
            station_longitude as lon,
            SUM(rides) as Rides
        FROM citi_statistics_by_week
        WHERE ride_week BETWEEN ? AND ?
        GROUP BY ALL
        ORDER BY ride_week
    """, [slider_min, slider_max]).df()
    
    if not df_map.empty:
        df_map['ride_week'] = df_map['ride_week'].astype(str)
        
        fig_anim = px.scatter_mapbox(
            df_map, lat="lat", lon="lon", size="Rides", color="Rides",
            animation_frame="ride_week",
            zoom=10, height=600,
            center=dict(lat=40.730610, lon=-73.935242),
            mapbox_style="carto-positron",
            color_continuous_scale=px.colors.sequential.Viridis,
            title="NYC Citi Bike Density"
        )
        
        fig_anim.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            sliders=[dict(
                active=0, currentvalue={"prefix": "Week: "}, pad={"t": 20},
                transition={"duration": 100, "easing": "linear"}
            )],
            updatemenus=[dict(
                type="buttons", showactive=True, x=0.03, y=0.05,
                buttons=[
                    dict(label="▶️ Play", method="animate", args=[None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]),
                    dict(label="⏸️ Stop", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
                ]
            )]
        )
        fig_anim.update_traces(marker=dict(opacity=0.7, sizemin=3, sizemode='area'))
        st.plotly_chart(fig_anim, use_container_width=True)
    else:
        st.warning("No data available for map in this date range.")
    
    st.info("NYC trippled the number of stations, aggressively expanding its network into boroughs surrounding Manhattan.")

    st.divider()

    # 2. BEHAVIORAL ANALYSIS
    st.subheader("🧠 Changing Habits: The 'Joyride' Effect")
    
    col_ny1, col_ny2 = st.columns(2)
    
    # Fetch NYC Behavioral Data
    df_ny_behav = con.execute("""
        SELECT 
            ride_week,
            SUM(rides) as total_rides,
            SUM(ride_duration_minutes) / SUM(rides) as avg_duration,
            SUM(CASE WHEN is_ride_weekend THEN rides ELSE 0 END) as weekend_rides,
            SUM(CASE WHEN is_ride_weekend THEN 0 ELSE rides END) as weekday_rides
        FROM citi_statistics_by_week
        WHERE ride_week BETWEEN ? AND ?
        GROUP BY 1
        ORDER BY 1
    """, [slider_min, slider_max]).df()

    with col_ny1:
        st.markdown("**1. The Duration Spike**")
        st.caption("Average trip length in minutes")
        fig_dur = px.area(
            df_ny_behav, x='ride_week', y='avg_duration',
            title='Average Trip Duration (Min)',
            color_discrete_sequence=['#003399']
        )
        fig_dur.add_vrect(x0="2020-03-20", x1="2021-01-01", fillcolor="orange", opacity=0.2, annotation_text="Lockdown")
        st.plotly_chart(fig_dur, use_container_width=True)
        st.info("During 2020, usage shifted from 'A-to-B' transport (short trips) to 'Leisure & Exercise' (long trips), with duration nearly doubling.")

    with col_ny2:
        st.markdown("**2. The Weekend Takeover**")
        st.caption("Total rides split by Weekday vs Weekend")
        # Melting for stacked bar chart
        df_ny_melt = df_ny_behav.melt(id_vars='ride_week', value_vars=['weekday_rides', 'weekend_rides'], var_name='Type', value_name='Rides')
        
        fig_weekend = px.bar(
            df_ny_melt, x='ride_week', y='Rides', color='Type',
            title='Weekday vs Weekend Volume',
            color_discrete_map={'weekday_rides': '#003399', 'weekend_rides': '#6699CC'}
        )
        st.plotly_chart(fig_weekend, use_container_width=True)
        st.info("While weekday commuting collapsed in 2020, weekend traffic exploded, driving the system's recovery.")


# ==============================================================================
# PAGE 3: LONDON DEEP DIVE (Improved)
# ==============================================================================
elif page == "🇬🇧 London Deep Dive":
    st.title("🇬🇧 London: The Missing Commuters")
    st.write("London's story is one of resilience but also a struggle to regain its core identity as a commuter network.")

    # Fetch London Data
    df_ldn_stats = con.execute("""
        SELECT 
            ride_week,
            SUM(rides) as total_rides,
            COUNT(DISTINCT start_station_name) as active_stations,
            SUM(CASE WHEN is_ride_rush_hour THEN rides ELSE 0 END) as rush_hour_rides,
            SUM(CASE WHEN is_ride_rush_hour THEN 0 ELSE rides END) as non_rush_hour_rides
        FROM tfl_statistics_by_week
        WHERE ride_week BETWEEN ? AND ?
        GROUP BY 1
        ORDER BY 1
    """, [slider_min, slider_max]).df()
    
    df_ldn_stats['rides_per_station'] = df_ldn_stats['total_rides'] / df_ldn_stats['active_stations']

    # 1. THE MAP ANIMATION
    st.subheader("📍 Hotspot Evolution")
    st.write("Visualize how ridership clusters shift over time across the city.")

    df_map = con.execute("""
        SELECT 
            ride_week,
            station_latitude as lat,
            station_longitude as lon,
            SUM(rides) as Rides
        FROM tfl_statistics_by_week
        WHERE ride_week BETWEEN ? AND ?
        GROUP BY ALL
        ORDER BY ride_week
    """, [slider_min, slider_max]).df()
    
    if not df_map.empty:
        df_map['ride_week'] = df_map['ride_week'].astype(str)
        
        fig_anim = px.scatter_mapbox(
            df_map, lat="lat", lon="lon", size="Rides", color="Rides",
            animation_frame="ride_week",
            zoom=10, height=600,
            center=dict(lat=51.512820, lon=-0.127171),
            mapbox_style="carto-positron",
            color_continuous_scale=px.colors.sequential.Viridis,
            title="London TFL Bike Density"
        )
        
        fig_anim.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            sliders=[dict(
                active=0, currentvalue={"prefix": "Week: "}, pad={"t": 20},
                transition={"duration": 100, "easing": "linear"}
            )],
            updatemenus=[dict(
                type="buttons", showactive=True, x=0.03, y=0.05,
                buttons=[
                    dict(label="▶️ Play", method="animate", args=[None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}]),
                    dict(label="⏸️ Stop", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
                ]
            )]
        )
        fig_anim.update_traces(marker=dict(opacity=0.7, sizemin=3, sizemode='area'))
        st.plotly_chart(fig_anim, use_container_width=True)
    else:
        st.warning("No data available for map in this date range.")

    st.info("Unlike NYC, London's station numbers remained flat.")

    st.divider()

    # 2. RUSH HOUR RECOVERY
    st.subheader("📉 Where did the commuters go?")
    st.write("Unlike NYC, London relies heavily on rush hour traffic. The chart below separates Commuter traffic (Dark Red) from Leisure traffic (Light Red).")
    
    # Melt for comparison
    df_ldn_melt = df_ldn_stats.melt(id_vars='ride_week', value_vars=['rush_hour_rides', 'non_rush_hour_rides'], var_name='Type', value_name='Rides')
    
    fig_rec = px.line(
        df_ldn_melt, x='ride_week', y='Rides', color='Type',
        title='Absolute Volume: Rush Hour vs Non-Rush Hour',
        color_discrete_map={'rush_hour_rides': '#DC241f', 'non_rush_hour_rides': '#ff9999'}
    )
    fig_rec.add_vrect(x0="2020-03-20", x1="2021-01-01", fillcolor="gray", opacity=0.1, annotation_text="Lockdowns", annotation_position="top left")
    st.plotly_chart(fig_rec, use_container_width=True)
    
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        st.info("Notice that **Non-Rush Hour** (Leisure) traffic actually hit record highs in 2021/2022. The system's 'slump' is almost entirely due to the missing **Rush Hour** commuters who haven't returned.")

    st.divider()

    # 3. NETWORK INTENSITY
    st.subheader("🥵 Sweating the Assets")
    st.write("London hasn't expanded its station count nearly as fast as NYC. This means the network is being worked harder.")

    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.caption("Total Active Stations")
        fig_stat = px.line(
            df_ldn_stats, x='ride_week', y='active_stations',
            title='Active Station Count',
            color_discrete_sequence=['gray']
        )
        st.plotly_chart(fig_stat, use_container_width=True)

    with col_stat2:
        st.caption("Rides per Station (Intensity)")
        fig_int = px.area(
            df_ldn_stats, x='ride_week', y='rides_per_station',
            title='Rides per Station',
            color_discrete_sequence=['#DC241f']
        )
        st.plotly_chart(fig_int, use_container_width=True)
    
    st.info("Even with fewer stations added, London maintains high efficiency. The network is dense and highly utilized, meaning station availability is likely a bigger challenge here than in the rapidly expanding NYC network.")