import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set page configuration
st.set_page_config(
    page_title="AeroSky — Premium Weather Dashboard",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look and feel
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom Card container */
    .metric-card {
        background-color: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.12);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border-color: rgba(128, 128, 128, 0.25);
    }
    
    /* Override Streamlit Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        opacity: 0.8;
    }
    
    /* Clean sidebar controls */
    section[data-testid="stSidebar"] {
        background-color: rgba(20, 20, 20, 0.02);
    }
    
    /* Subheaders and sections spacing */
    h2, h3 {
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    /* Custom button aesthetics */
    div.stButton > button {
        background: linear-gradient(135deg, #4A90E2, #50E3C2);
        color: white !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    div.stButton > button:hover {
        box-shadow: 0 4px 15px rgba(80, 227, 194, 0.4) !important;
        transform: translateY(-1px) !important;
        border: none !important;
    }
    
    /* Raw tables header styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Adjust map height */
    iframe[title="streamlit_map"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Shared session with retries
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))


# WMO Weather Codes mapping (Description, Emoji, CSS Background Gradient)
WMO_CODES = {
    0: ("Clear sky", "☀️", "linear-gradient(135deg, #FDEB71 10%, #F8D800 100%)"),
    1: ("Mainly clear", "🌤️", "linear-gradient(135deg, #FDEB71 10%, #F8D800 100%)"),
    2: ("Partly cloudy", "⛅", "linear-gradient(135deg, #ABDCFF 10%, #0396FF 100%)"),
    3: ("Overcast", "☁️", "linear-gradient(135deg, #757F9A 10%, #D7DDE8 100%)"),
    45: ("Fog", "🌫️", "linear-gradient(135deg, #E4E5E6 0%, #00416A 100%)"),
    48: ("Depositing rime fog", "🌫️", "linear-gradient(135deg, #E4E5E6 0%, #00416A 100%)"),
    51: ("Light drizzle", "🌧️", "linear-gradient(135deg, #81FBB8 10%, #28C76F 100%)"),
    53: ("Moderate drizzle", "🌧️", "linear-gradient(135deg, #81FBB8 10%, #28C76F 100%)"),
    55: ("Dense drizzle", "🌧️", "linear-gradient(135deg, #81FBB8 10%, #28C76F 100%)"),
    56: ("Light freezing drizzle", "🌧️", "linear-gradient(135deg, #2af598 0%, #009efd 100%)"),
    57: ("Dense freezing drizzle", "🌧️", "linear-gradient(135deg, #2af598 0%, #009efd 100%)"),
    61: ("Slight rain", "🌦️", "linear-gradient(135deg, #ABDCFF 10%, #0396FF 100%)"),
    63: ("Moderate rain", "🌧️", "linear-gradient(135deg, #90F7EC 0%, #32CCBC 100%)"),
    65: ("Heavy rain", "🌧️", "linear-gradient(135deg, #3B2667 10%, #BC78EC 100%)"),
    66: ("Light freezing rain", "🌧️", "linear-gradient(135deg, #2af598 0%, #009efd 100%)"),
    67: ("Heavy freezing rain", "🌧️", "linear-gradient(135deg, #2af598 0%, #009efd 100%)"),
    71: ("Slight snow fall", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    73: ("Moderate snow fall", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    75: ("Heavy snow fall", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    77: ("Snow grains", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    80: ("Slight rain showers", "🌦️", "linear-gradient(135deg, #ABDCFF 10%, #0396FF 100%)"),
    81: ("Moderate rain showers", "🌧️", "linear-gradient(135deg, #ABDCFF 10%, #0396FF 100%)"),
    82: ("Violent rain showers", "🌧️", "linear-gradient(135deg, #3B2667 10%, #BC78EC 100%)"),
    85: ("Slight snow showers", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    86: ("Heavy snow showers", "🌨️", "linear-gradient(135deg, #E3F2FD 10%, #90CAF9 100%)"),
    95: ("Thunderstorm", "⛈️", "linear-gradient(135deg, #F3904F 0%, #3B4371 100%)"),
    96: ("Thunderstorm with slight hail", "⛈️", "linear-gradient(135deg, #F3904F 0%, #3B4371 100%)"),
    99: ("Thunderstorm with heavy hail", "⛈️", "linear-gradient(135deg, #F3904F 0%, #3B4371 100%)"),
}

def get_weather_info(code):
    return WMO_CODES.get(code, ("Unknown", "❓", "linear-gradient(135deg, #8A2387 0%, #E94057 50%, #F27121 100%)"))

def get_wind_direction(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]

@st.cache_data(ttl=3600)
def geocode(name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": 10, "language": "en", "format": "json"}
    r = session.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])

@st.cache_data(ttl=600)
def fetch_weather(lat, lon, days=7, temp_unit="°C", wind_unit="km/h"):
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Map units to open-meteo query parameters
    api_temp_unit = "fahrenheit" if temp_unit == "°F" else "celsius"
    
    api_wind_unit = "kmh"
    if wind_unit == "mph":
        api_wind_unit = "mph"
    elif wind_unit == "m/s":
        api_wind_unit = "ms"
        
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,relativehumidity_2m,apparent_temperature,precipitation_probability,precipitation,weathercode,pressure_msl,windspeed_10m,uv_index",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max",
        "temperature_unit": api_temp_unit,
        "windspeed_unit": api_wind_unit,
        "forecast_days": days,
        "timezone": "auto",
    }
    r = session.get(url, params=params, timeout=15)
    if r.status_code == 429:
        raise Exception('Open-Meteo rate limit reached. Please try again in a few minutes.')
    r.raise_for_status()
    return r.json()

# Set standard city callback
def set_city(name, country, lat, lon, admin1=""):
    st.session_state.selected_city = {
        "name": name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "admin1": admin1
    }
    if "geocode_results" in st.session_state:
        del st.session_state.geocode_results

# Initialize default city in session state
if "selected_city" not in st.session_state:
    set_city("London", "United Kingdom", 51.5085, -0.1257, "England")

# Sidebar Branding
st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #4A90E2; font-size: 1.8rem; font-weight: 700;">⛅ AeroSky</h2>
        <p style="margin: 0; font-size: 0.85rem; opacity: 0.7;">Modern Weather Intelligence</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Sidebar - City Search
st.sidebar.markdown("### Search Location")
search_query = st.sidebar.text_input("Enter City", value=st.session_state.selected_city.get("name", "London"))
search_button = st.sidebar.button("Search Weather")

# Sidebar - Popular Cities Quick Access
st.sidebar.markdown("### Popular Cities")
cols_pop = st.sidebar.columns(2)
popular_cities = [
    ("London", "United Kingdom", 51.5085, -0.1257, "England"),
    ("New York", "United States", 40.7128, -74.0060, "New York"),
    ("Tokyo", "Japan", 35.6895, 139.6917, "Tokyo"),
    ("Paris", "France", 48.8566, 2.3522, "Île-de-France"),
    ("Sydney", "Australia", -33.8688, 151.2093, "New South Wales"),
    ("Mumbai", "India", 19.0760, 72.8777, "Maharashtra")
]

for idx, (name, country, lat, lon, admin1) in enumerate(popular_cities):
    col_idx = idx % 2
    if cols_pop[col_idx].button(f"{name}", key=f"quick_{name}", use_container_width=True):
        set_city(name, country, lat, lon, admin1)
        st.rerun()

# Sidebar - Display Settings
st.sidebar.markdown("### Settings")
temp_unit = st.sidebar.radio("Temperature Unit", options=["°C", "°F"], index=0)
wind_unit = st.sidebar.radio("Wind Speed Unit", options=["km/h", "mph", "m/s"], index=0)
days = st.sidebar.selectbox("Forecast Horizon", options=[1, 3, 5, 7], index=3)

# Handle Search Processing
if search_button and search_query.strip():
    with st.spinner("Searching for city..."):
        try:
            results = geocode(search_query.strip())
            if not results:
                st.sidebar.error("No locations found. Try another query.")
            elif len(results) == 1:
                set_city(
                    results[0].get("name"),
                    results[0].get("country"),
                    results[0].get("latitude"),
                    results[0].get("longitude"),
                    results[0].get("admin1", "")
                )
                st.rerun()
            else:
                st.session_state.geocode_results = results
        except Exception as e:
            st.sidebar.error(f"Geocoding failed: {e}")

# Resolve Geocode Choices
if "geocode_results" in st.session_state and st.session_state.geocode_results:
    results = st.session_state.geocode_results
    options = [
        f"{r.get('name')}, {r.get('country')} — {r.get('admin1','')}"
        f" ({r.get('latitude'):.2f}, {r.get('longitude'):.2f})"
        for r in results
    ]
    st.info("Multiple locations found. Please select your desired city:")
    selected_option = st.selectbox("Select City", options=options)
    if st.button("Confirm Selection", use_container_width=True):
        idx = options.index(selected_option)
        choice = results[idx]
        set_city(
            choice.get("name"),
            choice.get("country"),
            choice.get("latitude"),
            choice.get("longitude"),
            choice.get("admin1", "")
        )
        st.rerun()

# Fetch and Render Weather Dashboard
choice = st.session_state.selected_city
lat = choice.get("latitude")
lon = choice.get("longitude")
display_name = f"{choice.get('name')}, {choice.get('country')}"
if choice.get("admin1"):
    display_name = f"{choice.get('name')}, {choice.get('admin1')}, {choice.get('country')}"

with st.spinner("Retrieving weather forecast..."):
    try:
        data = fetch_weather(lat, lon, days=days, temp_unit=temp_unit, wind_unit=wind_unit)
    except Exception as e:
        st.error(f"Weather API request failed: {e}")
        st.stop()

current = data.get("current_weather", {})
hourly = data.get("hourly", {})
daily = data.get("daily", {})

if current:
    wcode = current.get("weathercode", 0)
    cond_desc, cond_emoji, gradient = get_weather_info(wcode)
    
    # 1. Title/Header Card
    st.markdown(
        f"""
        <div style="
            background: {gradient};
            padding: 30px;
            border-radius: 20px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.12);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        ">
            <div>
                <h1 style="margin: 0; font-size: 2.8rem; font-weight: 700; color: white;">{choice.get('name')}</h1>
                <p style="margin: 5px 0 0 0; font-size: 1.1rem; opacity: 0.95;">{choice.get('admin1') + ', ' if choice.get('admin1') else ''}{choice.get('country')}</p>
                <p style="margin: 5px 0 0 0; font-size: 0.85rem; opacity: 0.75;">Lat: {lat:.4f}° | Lon: {lon:.4f}°</p>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 4.5rem; line-height: 1;">{cond_emoji}</span>
                <div style="text-align: left;">
                    <div style="font-size: 3.5rem; font-weight: 700; line-height: 1;">{current.get('temperature')}{temp_unit}</div>
                    <div style="font-size: 1.25rem; font-weight: 500; opacity: 0.95; margin-top: 5px;">{cond_desc}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Find active hourly index for detailed metrics
    current_time_str = current.get("time")
    hourly_times = hourly.get("time", [])
    curr_idx = 0
    if current_time_str in hourly_times:
        curr_idx = hourly_times.index(current_time_str)
    else:
        try:
            current_time_dt = pd.to_datetime(current_time_str)
            hourly_dt = pd.to_datetime(hourly_times)
            curr_idx = (hourly_dt - current_time_dt).abs().argmin()
        except:
            pass
            
    # Extract hourly metrics safely
    feels_like = hourly.get("apparent_temperature", [])[curr_idx] if curr_idx < len(hourly.get("apparent_temperature", [])) else current.get("temperature")
    humidity = hourly.get("relativehumidity_2m", [])[curr_idx] if curr_idx < len(hourly.get("relativehumidity_2m", [])) else 50
    precip_prob = hourly.get("precipitation_probability", [])[curr_idx] if curr_idx < len(hourly.get("precipitation_probability", [])) else 0
    pressure = hourly.get("pressure_msl", [])[curr_idx] if curr_idx < len(hourly.get("pressure_msl", [])) else 1013
    
    # 2. Main Metrics Row
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric(
            label="Feels Like",
            value=f"{feels_like}{temp_unit}",
            delta=f"{round(feels_like - current.get('temperature'), 1)}{temp_unit} vs Actual"
        )
    with mcol2:
        st.metric(
            label="Humidity",
            value=f"{humidity}%",
            delta="Comfortable" if 30 <= humidity <= 60 else ("Humid" if humidity > 60 else "Dry")
        )
    with mcol3:
        st.metric(
            label="Wind Speed",
            value=f"{current.get('windspeed')} {wind_unit}",
            delta=f"Direction: {get_wind_direction(current.get('winddirection', 0))}"
        )
    with mcol4:
        st.metric(
            label="Precipitation Chance",
            value=f"{precip_prob}%",
            delta="No rain expected" if precip_prob < 20 else ("Likely rain" if precip_prob > 50 else "Possible showers")
        )

    # 3. Solar & Pressure Row
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    scol1, scol2, scol3 = st.columns(3)
    
    today_sunrise = daily.get("sunrise", [""])[0]
    today_sunset = daily.get("sunset", [""])[0]
    today_uv = daily.get("uv_index_max", [0.0])[0]
    
    try:
        sunrise_time = datetime.fromisoformat(today_sunrise).strftime("%I:%M %p")
        sunset_time = datetime.fromisoformat(today_sunset).strftime("%I:%M %p")
    except:
        sunrise_time = today_sunrise.split("T")[-1] if "T" in today_sunrise else today_sunrise
        sunset_time = today_sunset.split("T")[-1] if "T" in today_sunset else today_sunset
        
    with scol1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">☀️ Sunrise & Sunset</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-top: 8px;">🌅 {sunrise_time}</div>
                <div style="font-size: 1.5rem; font-weight: 700; margin-top: 4px;">🌇 {sunset_time}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with scol2:
        uv_caution = "Low"
        uv_color = "#2af598"
        if today_uv >= 8:
            uv_caution = "Very High (Use Protection!)"
            uv_color = "#FF007A"
        elif today_uv >= 6:
            uv_caution = "High (Wear Hat/Sunscreen)"
            uv_color = "#F3904F"
        elif today_uv >= 3:
            uv_caution = "Moderate"
            uv_color = "#F8D800"
            
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">⚡ Daily UV Max</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: {uv_color}; margin-top: 2px;">{today_uv}</div>
                <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">{uv_caution}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with scol3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; opacity: 0.8; font-weight: 500;">🎈 Atmospheric Pressure</div>
                <div style="font-size: 2.2rem; font-weight: 700; margin-top: 2px;">{pressure} hPa</div>
                <div style="font-size: 0.85rem; font-weight: 500; opacity: 0.9;">Baseline: 1013 hPa</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# 4. Hourly Forecast Analytics Chart Section
st.markdown("<hr style='opacity: 0.15; margin: 25px 0;'>", unsafe_allow_html=True)
if hourly:
    df_hourly = pd.DataFrame({
        "time": pd.to_datetime(hourly.get("time", [])),
        "temperature": hourly.get("temperature_2m", []),
        "feels_like": hourly.get("apparent_temperature", []),
        "humidity": hourly.get("relativehumidity_2m", []),
        "precipitation": hourly.get("precipitation", []),
        "precipitation_probability": hourly.get("precipitation_probability", []),
        "wind_speed": hourly.get("windspeed_10m", []),
        "pressure": hourly.get("pressure_msl", []),
        "uv_index": hourly.get("uv_index", [])
    })
    
    if not df_hourly.empty:
        st.subheader("Hourly Forecast Analytics")
        tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Profile", "💧 Rain & Humidity", "💨 Wind & Pressure"])
        
        # Temp Chart
        with tab1:
            df_temp = df_hourly[["time", "temperature", "feels_like"]].melt("time", var_name="Type", value_name="Temp")
            df_temp["Type"] = df_temp["Type"].map({"temperature": "Actual Temp", "feels_like": "Feels Like"})
            
            temp_chart = alt.Chart(df_temp).mark_line(interpolate="monotone", strokeWidth=2.5).encode(
                x=alt.X("time:T", title="Time"),
                y=alt.Y("Temp:Q", title=f"Temperature ({temp_unit})", scale=alt.Scale(zero=False)),
                color=alt.Color("Type:N", title="Legend", scale=alt.Scale(domain=["Actual Temp", "Feels Like"], range=["#FF5A5F", "#4A90E2"])),
                tooltip=[
                    alt.Tooltip("time:T", format="%A, %b %d, %H:%M"),
                    alt.Tooltip("Temp:Q", format=".1f")
                ]
            ).properties(
                height=350
            ).interactive()
            
            st.altair_chart(temp_chart, use_container_width=True)
            
        # Rain Chart
        with tab2:
            base_rain = alt.Chart(df_hourly).encode(x=alt.X("time:T", title="Time"))
            
            bar_rain = base_rain.mark_bar(color="#50E3C2", opacity=0.6).encode(
                y=alt.Y("precipitation:Q", title="Precipitation (mm)", axis=alt.Axis(titleColor="#32CCBC")),
                tooltip=[
                    alt.Tooltip("time:T", format="%A, %b %d, %H:%M"),
                    alt.Tooltip("precipitation:Q", title="Precipitation (mm)", format=".2f")
                ]
            )
            
            line_rain = base_rain.mark_line(color="#4A90E2", interpolate="monotone", strokeWidth=2).encode(
                y=alt.Y("precipitation_probability:Q", title="Rain Probability (%)", axis=alt.Axis(titleColor="#4A90E2")),
                tooltip=[
                    alt.Tooltip("time:T", format="%A, %b %d, %H:%M"),
                    alt.Tooltip("precipitation_probability:Q", title="Probability (%)")
                ]
            )
            
            rain_chart = alt.layer(bar_rain, line_rain).resolve_scale(
                y="independent"
            ).properties(
                height=350
            ).interactive()
            
            st.altair_chart(rain_chart, use_container_width=True)
            
        # Wind/Pressure Chart
        with tab3:
            base_wp = alt.Chart(df_hourly).encode(x=alt.X("time:T", title="Time"))
            
            wind_line = base_wp.mark_area(
                color="#F3904F",
                opacity=0.3,
                line={"color": "#F3904F", "strokeWidth": 2},
                interpolate="monotone"
            ).encode(
                y=alt.Y("wind_speed:Q", title=f"Wind Speed ({wind_unit})", axis=alt.Axis(titleColor="#F3904F")),
                tooltip=[
                    alt.Tooltip("time:T", format="%A, %b %d, %H:%M"),
                    alt.Tooltip("wind_speed:Q", title=f"Wind Speed ({wind_unit})", format=".1f")
                ]
            )
            
            pressure_line = base_wp.mark_line(color="#757F9A", interpolate="monotone", strokeWidth=2).encode(
                y=alt.Y("pressure:Q", title="Atmospheric Pressure (hPa)", scale=alt.Scale(zero=False), axis=alt.Axis(titleColor="#757F9A")),
                tooltip=[
                    alt.Tooltip("time:T", format="%A, %b %d, %H:%M"),
                    alt.Tooltip("pressure:Q", title="Pressure (hPa)", format=".1f")
                ]
            )
            
            wind_press_chart = alt.layer(wind_line, pressure_line).resolve_scale(
                y="independent"
            ).properties(
                height=350
            ).interactive()
            
            st.altair_chart(wind_press_chart, use_container_width=True)

# 5. Daily Forecast Section
st.markdown("<hr style='opacity: 0.15; margin: 25px 0;'>", unsafe_allow_html=True)
if daily:
    st.subheader(f"Upcoming {days}-Day Forecast")
    d_cols = st.columns(days)
    
    for i in range(days):
        d_time = daily.get("time", [])[i]
        d_code = daily.get("weathercode", [])[i]
        d_max = daily.get("temperature_2m_max", [])[i]
        d_min = daily.get("temperature_2m_min", [])[i]
        d_precip_prob = daily.get("precipitation_probability_max", [0])[i]
        d_uv = daily.get("uv_index_max", [0.0])[i]
        
        # Format the date
        dt = datetime.strptime(d_time, "%Y-%m-%d")
        day_name = dt.strftime("%a")
        date_str = dt.strftime("%b %d")
        
        d_desc, d_emoji, d_grad = get_weather_info(d_code)
        
        with d_cols[i]:
            st.markdown(
                f"""
                <div style="
                    background: {d_grad};
                    color: white;
                    border-radius: 12px;
                    padding: 15px 10px;
                    text-align: center;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                ">
                    <div style="font-weight: 700; font-size: 1.1rem; line-height: 1.2;">{day_name}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 8px;">{date_str}</div>
                    <div style="font-size: 2.2rem; margin: 8px 0;">{d_emoji}</div>
                    <div style="font-weight: 600; font-size: 0.85rem; opacity: 0.95; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{d_desc}</div>
                    <div style="font-weight: 700; font-size: 1.15rem; margin-top: 8px;">
                        {round(d_max)}° / {round(d_min)}°
                    </div>
                    <div style="font-size: 0.75rem; opacity: 0.9; margin-top: 6px;">
                        💧 {d_precip_prob}% | UV {round(d_uv)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# 6. Location Map & Tabular Section
st.markdown("<hr style='opacity: 0.15; margin: 25px 0;'>", unsafe_allow_html=True)
col_map, col_raw = st.columns([1, 1])

with col_map:
    st.subheader("Location Map")
    map_df = pd.DataFrame({
        "lat": [lat],
        "lon": [lon]
    })
    st.map(map_df, zoom=9, use_container_width=True)

with col_raw:
    st.subheader("Raw Forecast Data")
    if not df_hourly.empty:
        df_raw = df_hourly.copy()
        df_raw.rename(columns={
            "time": "Time",
            "temperature": f"Temp ({temp_unit})",
            "feels_like": f"Feels Like ({temp_unit})",
            "humidity": "Humidity (%)",
            "precipitation": "Rain (mm)",
            "precipitation_probability": "Rain Prob (%)",
            "wind_speed": f"Wind ({wind_unit})",
            "pressure": "Pressure (hPa)",
            "uv_index": "UV Index"
        }, inplace=True)
        st.dataframe(df_raw.set_index("Time"), height=300)
    else:
        st.info("No hourly data is currently populated.")


# Footer
st.markdown("<hr style='opacity: 0.1;'>", unsafe_allow_html=True)
st.caption("AeroSky Weather intelligence. Data dynamically retrieved from Open-Meteo. No API Key required.")
