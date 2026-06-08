import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title="Weather App", layout="wide")

st.title("Simple Weather App — Open-Meteo")

st.markdown("Enter a city name (e.g. London, New York, Tokyo) and click 'Get weather'.")

col1, col2 = st.columns([2, 1])

with col1:
    city = st.text_input("City", value="London")
    search = st.button("Get weather")

with col2:
    days = st.selectbox("Forecast days", options=[1, 2, 3, 5, 7], index=1)


def geocode(name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "count": 5, "language": "en", "format": "json"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


def fetch_weather(lat, lon, days=2):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": ",".join(["temperature_2m", "relativehumidity_2m", "precipitation"]),
        "forecast_days": days,
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


if search and city.strip():
    with st.spinner("Searching for location..."):
        try:
            results = geocode(city.strip())
        except Exception as e:
            st.error(f"Geocoding failed: {e}")
            st.stop()

    if not results:
        st.error("No locations found for that query.")
    else:
        if len(results) == 1:
            choice = results[0]
        else:
            options = [f"{r.get('name')}, {r.get('country')} — {r.get('admin1','')} ({r.get('latitude'):.4f},{r.get('longitude'):.4f})" for r in results]
            idx = st.selectbox("Multiple locations found — choose one", options=options, format_func=lambda x: x)
            choice = results[options.index(idx)]

        lat = choice.get("latitude")
        lon = choice.get("longitude")
        display_name = f"{choice.get('name')}, {choice.get('country')}"

        with st.spinner(f"Fetching weather for {display_name}..."):
            try:
                data = fetch_weather(lat, lon, days=days)
            except Exception as e:
                st.error(f"Weather API failed: {e}")
                st.stop()

        # Current weather
        current = data.get("current_weather", {})
        st.subheader(f"Current weather — {display_name}")
        if current:
            ccol1, ccol2, ccol3, ccol4 = st.columns(4)
            ccol1.metric("Temperature (°C)", current.get("temperature"))
            ccol2.metric("Windspeed (m/s)", current.get("windspeed"))
            ccol3.metric("Wind direction (°)", current.get("winddirection"))
            time_str = current.get("time")
            ccol4.write(f"Time: {time_str}")

        # Hourly data frame
        hourly = data.get("hourly", {})
        if hourly:
            df = pd.DataFrame({
                "time": hourly.get("time", []),
                "temperature": hourly.get("temperature_2m", []),
                "humidity": hourly.get("relativehumidity_2m", []),
                "precipitation": hourly.get("precipitation", []),
            })
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                st.subheader("Hourly forecast")
                line = alt.Chart(df).mark_line().encode(x="time:T", y=alt.Y("temperature:Q", title="Temperature (°C)"))
                points = alt.Chart(df).mark_point(size=10).encode(x="time:T", y="temperature:Q", tooltip=["time:T", "temperature", "humidity", "precipitation"])
                st.altair_chart(line + points, use_container_width=True)

                st.subheader("Raw hourly data")
                st.dataframe(df.set_index("time"))
        else:
            st.info("No hourly data available.")

        st.markdown("---")
        st.caption("Data provided by Open-Meteo (no API key required)")
