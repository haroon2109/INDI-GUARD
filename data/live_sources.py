import requests
import pandas as pd
import random
import json
import os
from datetime import datetime

# --- CONFIGURATION ---
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
USGS_EARTHQUAKE_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

CACHE_FILE = "data/offline_cache.json"

def save_to_cache(data):
    """Saves data to a local JSON file for offline access."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Cache write failed: {e}")

def load_from_cache():
    """Loads data from local JSON cache."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Cache read failed: {e}")
    return None

def fetch_weather_data(lat, lon):
    """
    Fetches current weather data from Open-Meteo API.
    """
    try:
        # Secure API Handling: Check Streamlit Secrets first, then Environment Variables
        try:
            import streamlit as st
            # api_key = st.secrets.get("OPENWEATHER_API_KEY") # Example for protected APIs
        except ImportError:
            pass
            
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "hourly": "temperature_2m,relativehumidity_2m,rain,surface_pressure,windspeed_10m",
            "timezone": "auto"
        }
        # if api_key: params['appid'] = api_key
        response = requests.get(OPEN_METEO_URL, params=params, timeout=5)
        data = response.json()
        
        current = data.get('current_weather', {})
        
        result = {
            "Temperature": current.get('temperature', 25.0),
            "WindSpeed": current.get('windspeed', 10.0),
            "WindDirection": current.get('winddirection', 0),
            "Rainfall": 0.0, 
            "status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Update Cache (simplistic global cache for demo)
        save_to_cache({"weather": result})
        return result
        
    except Exception as e:
        print(f"Live fetch failed ({e}). Attempting offline mode...")
        cached = load_from_cache()
        if cached and "weather" in cached:
            cached["weather"]["status"] = "offline_cache"
            return cached["weather"]
            
        return {"status": "error", "Temperature": 25.0, "WindSpeed": 5.0, "Rainfall": 0.0}

def fetch_seismic_data():
    """
    Fetches earthquake data from USGS (Global, filtered for India region roughly).
    """
    try:
        response = requests.get(USGS_EARTHQUAKE_URL)
        data = response.json()
        
        quakes = []
        for feature in data['features']:
            props = feature['properties']
            geo = feature['geometry']['coordinates'] # lon, lat, depth
            
            # Rough bounding box for India: Lat 6-37, Lon 68-98
            lon, lat, depth = geo[0], geo[1], geo[2]
            
            if 6 <= lat <= 37 and 68 <= lon <= 98:
                quakes.append({
                    "Place": props['place'],
                    "Magnitude": props['mag'],
                    "Time": datetime.fromtimestamp(props['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    "Latitude": lat,
                    "Longitude": lon,
                    "Depth": depth
                })
        
        return pd.DataFrame(quakes)
    except Exception as e:
        print(f"Error fetching seismic data: {e}")
        return pd.DataFrame()

def get_mock_disaster_alerts():
    """
    Simulates official alerts from ITEWC/INCOIS/IMD.
    """
    alerts = []
    
    # 1. Random Cyclone Alert
    if random.random() < 0.3:
        alerts.append({
            "Type": "Cyclone",
            "Level": "Severe",
            "Location": "Odisha Coast",
            "Message": "Severe Cyclonic Storm approaching. Landfall expected in 24 hours."
        })
        
    # 2. Random Tsunami Watch
    if random.random() < 0.1:
        alerts.append({
            "Type": "Tsunami",
            "Level": "Watch",
            "Location": "Andaman & Nicobar Islands",
            "Message": "Minor sea level fluctuations observed."
        })
        
    return alerts
