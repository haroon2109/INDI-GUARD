import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import time
from datetime import datetime
from data.live_sources import fetch_weather_data, fetch_seismic_data, get_mock_disaster_alerts
from ui_translations import get_text
from cap_utils import generate_cap_xml
from pdf_report import generate_sitrep
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- CONFIGURATION ---
st.set_page_config(page_title="IndiGuard Platform", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; color: #333; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    .stAlert { font-weight: 600; border-radius: 8px; }
    .ticker-wrap {
        width: 100%;
        background-color: #eee;
        overflow: hidden;
        white-space: nowrap;
        padding: 10px;
        border-bottom: 2px solid #ddd;
    }
    .ticker-item { display: inline-block; padding: 0 2rem; font-weight: bold; color: #d9534f; }
</style>
""", unsafe_allow_html=True)

# --- LOAD RESOURCES ---
@st.cache_resource
def load_resources():
    try:
        model = joblib.load('model/disaster_model.pkl')
        region_enc = joblib.load('model/region_encoder.pkl')
        season_enc = joblib.load('model/season_encoder.pkl')
        target_enc = joblib.load('model/target_encoder.pkl')
        scaler = joblib.load('model/scaler.pkl')
        df = pd.read_csv('data/disaster_data.csv')
        idrn = pd.read_csv('data/idrn_mock.csv')
        return model, region_enc, season_enc, target_enc, scaler, df, idrn
    except Exception as e:
        return None, None, None, None, None, None, None

model, region_enc, season_enc, target_enc, scaler, df, idrn_db = load_resources()

if model is None:
    st.error("🚨 System Initialization Failed. Please run `generate_data.py` and `train_model.py`.")
    st.stop()

# --- HEADER & TICKER ---
lang = st.sidebar.radio("Language / भाषा", ["English", "Hindi", "Tamil"], horizontal=True)

# News Ticker (Simulated Live Feed)
alerts = get_mock_disaster_alerts()
ticker_text = " | ".join([f"{a['Type'].upper()}: {a['Message']}" for a in alerts])
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker-item">🔴 LIVE ALERTS: {ticker_text} | IMD: Heavy rains expected in Odisha | NCS: No recent large earthquakes.</div>
</div>
""", unsafe_allow_html=True)

# --- HEARTBEAT & TITLE ---
c_title, c_beat = st.columns([3, 1])

with c_title:
    st.title(get_text(lang, 'title'))
    st.markdown(f"**{get_text(lang, 'subtitle')}**")

# Placeholder for Heartbeat (to be updated after data fetch)
beat_placeholder = c_beat.empty()

# --- SIDEBAR (CONTROL TOWER) ---

# 1. Scope Selection
with st.sidebar.expander("🌍 Location & Scope", expanded=True):
    role = st.selectbox("View Mode", ["Citizen", "Official", "Researcher"])
    regions = sorted(df['Region'].unique())
    selected_region = st.selectbox(get_text(lang, 'region'), regions)
    selected_date = st.date_input(get_text(lang, 'date'))
    
    # Advanced Geospatial Search
    st.markdown("---")
    search_loc = st.text_input("📍 Search Village/City", placeholder="e.g. Puri, Odisha")

# 2. Hazard Filters & Units
with st.sidebar.expander("⚠️ Settings & Filters", expanded=True):
    disaster_type = st.multiselect(get_text(lang, 'disaster_type'), 
                                   ["Weather", "Flood", "Cyclone", "Earthquake", "Tsunami", "Drought"],
                                   default=["Weather", "Flood"])
    use_live = st.checkbox(get_text(lang, 'live_data'))
    use_imperial = st.checkbox("🇺🇸 Imperial Units (°F, mph)", value=False)
    
    # Download Raw Data
    csv_data = df[df['Region'] == selected_region].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Region Data (CSV)", csv_data, f"{selected_region}_data.csv", "text/csv")

# Defaults logic
defaults = df[df['Region'] == selected_region].mean(numeric_only=True)
lat_ref = float(defaults.get('Latitude', 20.0))
lon_ref = float(defaults.get('Longitude', 78.0))

# Geocoding Logic
if search_loc:
    try:
        geolocator = Nominatim(user_agent="disaster_guard_ai_india")
        location = geolocator.geocode(search_loc + ", India", timeout=10)
        if location:
            lat_ref = location.latitude
            lon_ref = location.longitude
            st.sidebar.success(f"Found: {location.address}")
        else:
            st.sidebar.error("Location not found.")
    except Exception as e:
        st.sidebar.error(f"Search Error: {e}")

temp_default = float(defaults.get('Temperature', 30))
wind_default = float(defaults.get('WindSpeed', 10))

# Live Data Fetching
@st.cache_data(ttl=3600)
def get_weather_optimized(lat, lon):
    return fetch_weather_data(lat, lon)

status_emoji = "⚪"
if use_live:
    live_w = get_weather_optimized(lat_ref, lon_ref)
    if live_w['status'] == 'success':
        status_emoji = "🟢"
        temp_default = live_w['Temperature']
        wind_default = live_w['WindSpeed']
    elif live_w['status'] == 'offline_cache':
        status_emoji = "🟠"
        temp_default = live_w['Temperature']
        wind_default = live_w['WindSpeed']

# 3. What-If Simulation Controls
with st.sidebar.expander("🎛️ What-If Simulation", expanded=True):
    st.caption("Adjust sliders to simulate disaster scenarios. Values override live data.")
    
    # Unit Conversions for Display
    u_temp = "°F" if use_imperial else "°C"
    u_wind = "mph" if use_imperial else "km/h"
    u_rain = "in" if use_imperial else "mm"
    
    def to_imp(val, type_):
        if not use_imperial: return val
        if type_ == 'c_to_f': return (val * 9/5) + 32
        if type_ == 'km_to_mi': return val * 0.621371
        if type_ == 'mm_to_in': return val * 0.0393701
        return val

    # Sliders (Logic handles metric internally, display converts)
    st.markdown("**🌧️ Weather & Atmosphere**")
    
    # Rainfall
    r_val = st.slider(f"Rainfall ({u_rain})", 0.0, to_imp(600.0, 'mm_to_in'), to_imp(float(defaults.get('Rainfall', 100.0)), 'mm_to_in'))
    rainfall = r_val / 0.0393701 if use_imperial else r_val
    
    # Wind
    w_val = st.slider(f"Wind Speed ({u_wind})", 0.0, to_imp(250.0, 'km_to_mi'), to_imp(wind_default, 'km_to_mi'))
    wind_speed = w_val / 0.621371 if use_imperial else w_val
    
    # Temp
    t_val = st.slider(f"Temperature ({u_temp})", to_imp(-10.0, 'c_to_f'), to_imp(50.0, 'c_to_f'), to_imp(temp_default, 'c_to_f'))
    temperature = (t_val - 32) * 5/9 if use_imperial else t_val
    
    humidity = st.slider(get_text(lang, 'humidity'), 0.0, 100.0, float(defaults.get('Humidity', 60.0)))
    pressure = st.slider("Pressure (hPa)", 900.0, 1050.0, float(defaults.get('Pressure', 1010)))
    
    st.markdown("**🌊 Hydrology & Land**")
    river_level = st.slider("River Level (m)", 0.0, 20.0, float(defaults.get('RiverLevel', 5)))
    soil_moisture = st.slider("Soil Moisture", 0.0, 100.0, float(defaults.get('SoilMoisture', 50)))
    
    st.markdown("**🏙️ Vulnerability Factors**")
    infra_index = st.slider("Infra Index (1-10)", 1.0, 10.0, float(defaults.get('InfrastructureIndex', 5)))
    pop_density = st.number_input("Pop Density (per sq.km)", 100, 50000, 1000)
    
    if use_live:
        st.info(f"ℹ️ Live Data: {status_emoji} Active")

# 4. 🛠️ Developer & Stress Test
with st.sidebar.expander("🛠️ Developer & Stress Test", expanded=False):
    st.caption("Simulate high-load scenarios to test offline resilience.")
    run_stress = st.toggle("Simulate Heavy Load (700+ Districts)")
    enable_optim = st.checkbox("Enable Geometry Simplification", value=True)
    
    st.markdown("---")
    kiosk_mode = st.toggle("🖥️ Kiosk Mode (Command Center)")
    auto_refresh = st.checkbox("Enable Auto-Refresh (5m)")

    if run_stress:
        st.info("Loading heavy GeoJSON...")
        
    if kiosk_mode:
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            header { visibility: hidden; }
            .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
        </style>
        """, unsafe_allow_html=True)
        
    if auto_refresh:
        import time
        time_placeholder = st.empty()
        # Simple Rerun every 300s
        # Note: This stops the script from being interactive if we sleep main thread. 
        # Better to Use Streamlit's fragment or just a simple check.
        # For this demo, we can assume manual refresh is preferred unless we use st_autorefresh.
        # Let's skip the blocking sleep and rely on a meta refresh or similar if critical.
        st.markdown(
            """
            <script>
                setTimeout(function(){
                   window.location.reload(1);
                }, 300000);
            </script>
            """,
            unsafe_allow_html=True
        )

# Update Heartbeat
# Placeholder for the heartbeat status
beat_placeholder = st.sidebar.empty()

# --- ENGINE ---
def predict_ibf():
    r_code = region_enc.transform([selected_region])[0]
    curr_season = "Monsoon" if rainfall > 200 else "Summer"
    try: s_code = season_enc.transform([curr_season])[0]
    except: s_code = 0 

    raw = [[rainfall, temperature, humidity, soil_moisture, river_level, wind_speed, pressure, pop_density, infra_index]]
    scaled = scaler.transform(raw)[0]
    features = [[r_code, s_code] + list(scaled)]
    
    probs = model.predict_proba(features)[0]
    high_idx = list(target_enc.classes_).index('High')
    likelihood_score = probs[high_idx]
    
    vuln_score = (pop_density / 5000) + (10 - infra_index)
    vuln_norm = min(vuln_score / 15.0, 1.0)
    
    ibf_risk_score = (likelihood_score * 0.6) + (vuln_norm * 0.4)
    if ibf_risk_score > 0.7: final_risk = "High"
    elif ibf_risk_score > 0.4: final_risk = "Moderate"
    else: final_risk = "Low"
    
    return final_risk, ibf_risk_score, likelihood_score, vuln_norm

current_risk, risk_score, likelihood, vulnerability = predict_ibf()



beat_color = "#999" # Grey for Sim
beat_text = "SIMULATION MODE"

if use_live:
    if status_emoji == "🟢":
        beat_color = "#28a745" # Green
        beat_text = f"LIVE SYNC | {datetime.now().strftime('%H:%M')}"
    elif status_emoji == "🟠":
        beat_color = "#ffc107" # Orange
        beat_text = f"OFFLINE CACHE | {datetime.now().strftime('%H:%M')}"
    else:
        beat_color = "#dc3545" # Red
        beat_text = "CONN. ERROR"

beat_html = f"""
<style>
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 {beat_color}bb; }}
    70% {{ box-shadow: 0 0 0 10px {beat_color}00; }}
    100% {{ box-shadow: 0 0 0 0 {beat_color}00; }}
}}
.heartbeat {{
    width: 12px; height: 12px; background-color: {beat_color};
    border-radius: 50%; display: inline-block; margin-right: 8px;
    animation: pulse 2s infinite;
}}
.status-text {{ color: {beat_color}; font-weight: bold; font-family: monospace; font-size: 0.9rem; }}
</style>
<div style="text-align: right; padding-top: 25px;">
    <span class="heartbeat"></span>
    <span class="status-text">{beat_text}</span>
</div>
"""
beat_placeholder.markdown(beat_html, unsafe_allow_html=True)

# --- ENGINE ---

# --- DASHBOARD (THE GOLDEN GRID) ---

# 1. KPI ROW
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
color_map = {'High': 'inverse', 'Moderate': 'off', 'Low': 'normal'} 

with kpi1:
    st.metric(label="Risk Level", value=current_risk.upper(), delta="Stable" if current_risk=='Low' else "Critical")
with kpi2:
    st.metric(label="Pop. at Risk (Est.)", value=f"{int(pop_density * 5):,}", delta="High Vulnerability", delta_color="inverse")
with kpi3:
    threat = "Flood" if rainfall > 200 else "Cyclone" if wind_speed > 80 else "None"
    st.metric(label="Primary Threat", value=threat)
with kpi4:
    shelter_cap = 5000 if current_risk == 'High' else 2000
    st.metric(label="Shelter Capacity", value=f"{shelter_cap} ppl", delta="Available")

# 2. MAP ROW (HERO)
st.markdown("### 🗺️ Operational Picture")
m = folium.Map(location=[lat_ref, lon_ref], zoom_start=10, tiles=None)

# Layers
# 1. Dark Mode
folium.TileLayer(
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr=' ',
    name="Dark Mode (Night Ops)"
).add_to(m)

# 2. Satellite (Esri)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr=' ', 
    name='Satellite View',
    overlay=False
).add_to(m)

# 3. Daylight (Street)
folium.TileLayer(
    tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attr=' ',
    name='Street View'
).add_to(m)

# Stress Test Layer
if run_stress:
    try:
        import geopandas as gpd
        import time
        t_start = time.time()
        import os
        if not os.path.exists('data/india_districts_mock.geojson'):
             st.warning("GeoJSON missing. Generating...")
             import data.generate_heavy_geojson as gen
             gen.generate_heavy_geojson()
             
        gdf = gpd.read_file('data/india_districts_mock.geojson')
        raw_count = len(gdf)
        status_msg = f"Loaded {raw_count} polygons in {time.time() - t_start:.2f}s. "
        
        if enable_optim:
            t_opt = time.time()
            gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.05, preserve_topology=True)
            status_msg += f"Simplified in {time.time() - t_opt:.2f}s. "
            
        folium.GeoJson(
            gdf,
            name="Stress Test (Districts)",
            style_function=lambda x: {'fillColor': '#ffaf00', 'color': 'black', 'weight': 1, 'fillOpacity': 0.4},
            tooltip=folium.GeoJsonTooltip(fields=['name', 'risk_score'])
        ).add_to(m)
        st.success(f"✅ {status_msg}")
    except Exception as e:
        st.error(f"Stress Test Failed: {e}")

# Risk Zone (Hide if Stress Test is active)
if not run_stress:
    folium.Polygon(
        locations=[[lat_ref + 0.1, lon_ref + 0.1], [lat_ref + 0.1, lon_ref - 0.1],
                [lat_ref - 0.1, lon_ref - 0.1], [lat_ref - 0.1, lon_ref + 0.1]],
        color="red" if current_risk == 'High' else "orange",
        fill=True, fill_opacity=0.3, popup="Risk Zone", name="Hazard Zone"
    ).add_to(m)

# Layer 3: Resources
if idrn_db is not None:
    fg_res = folium.FeatureGroup(name="IDRN Resources")
    for _, row in idrn_db.iterrows():
        icon_color = 'blue' if row['Type'] == 'NDRF' else 'green'
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"<b>{row['Type']}</b>: {row['Name']}",
            icon=folium.Icon(color=icon_color, icon='user')
        ).add_to(fg_res)
    fg_res.add_to(m)

# Layer 4: Live Alerts Hierarchy (Pulse & Verification)
fg_alerts = folium.FeatureGroup(name="🚨 Live Alerts (Hierarchy)")
# Mock Live Alerts Data
mock_alerts = [
    {"loc": [lat_ref + 0.05, lon_ref - 0.05], "type": "Flood", "severity": "High", "verified": True},
    {"loc": [lat_ref - 0.08, lon_ref + 0.02], "type": "Storm", "severity": "Moderate", "verified": False},
    {"loc": [lat_ref + 0.12, lon_ref + 0.08], "type": "Heatwave", "severity": "Low", "verified": True},
]
for a in mock_alerts:
    is_high = a['severity'] == "High"
    is_verified = a['verified']
    size = 40 if is_high else 20
    color = "red" if is_high else "orange" if a['severity'] == "Moderate" else "yellow"
    border = "solid" if is_verified else "dashed"
    anim = "pulse-alert" if is_high else ""
    
    icon_html = f"""
    <div class="{anim}" style="
        width: {size}px; height: {size}px;
        background-color: {color};
        border: 3px {border} white;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; color: white; font-size: {int(size/2)}px;
    ">!</div>
    """
    folium.Marker(
        a['loc'],
        icon=folium.DivIcon(html=icon_html),
        popup=folium.Popup(f"<b>{a['type']}</b><br>Severity: {a['severity']}<br>Verified: {a['verified']}", max_width=200)
    ).add_to(fg_alerts)
fg_alerts.add_to(m)

folium.LayerControl().add_to(m)

# Add Legend (Floating HTML)
legend_html = '''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 130px; 
     border:2px solid grey; z-index:9999; font-size:12px;
     background-color:white; opacity: 0.8; padding: 10px;">
     <b>Map Legend</b><br>
     <i style="background:red; width:10px; height:10px; display:inline-block; border-radius:50%"></i> High Risk (Pulse)<br>
     <i style="background:orange; width:10px; height:10px; display:inline-block; border-radius:50%"></i> Mod Risk Zone<br>
     <i style="border: 2px solid black; width:10px; height:10px; display:inline-block;"></i> Solid=Verified<br>
     <i style="border: 2px dashed black; width:10px; height:10px; display:inline-block;"></i> Dash=Unverified<br>
     <i style="color:blue" class="fa fa-map-marker"></i> Resources
      </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=None, height=500)

# CSS for Alert Pulse
st.markdown("""
<style>
@keyframes pulse-alert {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
    50% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
}
.pulse-alert { animation: pulse-alert 1.5s infinite; }
</style>
""", unsafe_allow_html=True)


# 3. ANALYTICS & ACTIONS ROW
c1, c2 = st.columns([1, 1])

with c1:
    st.markdown("### 📊 Advanced Analytics")
    
    # Tabs for various analytical views
    tab_matrix, tab_trend, tab_dist, tab_corr = st.tabs(["Risk Matrix", "📉 Trends", "📊 Distributions", "🔗 Correlations"])
    
    with tab_matrix:
        # IMPROVED RISK MATRIX (Scatter on Color Grid)
        # Likelihood (Y) vs Impact/Vulnerability (X)
        
        # Create background colored zones
        shapes = [
            # Low Risk (Green) - Bottom Left
            dict(type="rect", x0=0, y0=0, x1=0.5, y1=0.5, fillcolor="rgba(0,255,0,0.2)", line=dict(width=0)),
            # Moderate Risk (Yellow) - Top Left & Bottom Right
            dict(type="rect", x0=0, y0=0.5, x1=0.5, y1=1, fillcolor="rgba(255,165,0,0.2)", line=dict(width=0)),
            dict(type="rect", x0=0.5, y0=0, x1=1, y1=0.5, fillcolor="rgba(255,165,0,0.2)", line=dict(width=0)),
            # High Risk (Red) - Top Right
            dict(type="rect", x0=0.5, y0=0.5, x1=1, y1=1, fillcolor="rgba(255,0,0,0.2)", line=dict(width=0)),
        ]
        
        fig_mat = go.Figure()
        
        # Add Current Status Point
        fig_mat.add_trace(go.Scatter(
            x=[vulnerability], y=[likelihood],
            mode='markers+text',
            text=['📍 THIS EVENT'], textposition="top center",
            marker=dict(size=25, color='black', symbol='x'),
            name='Current Status'
        ))
        
        fig_mat.update_layout(
            title="Dynamic Risk Matrix",
            xaxis=dict(title="Impact (Vulnerability)", range=[0, 1], showgrid=False),
            yaxis=dict(title="Likelihood (Probability)", range=[0, 1], showgrid=False),
            shapes=shapes,
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_mat, use_container_width=True)
        st.caption(f"x: {vulnerability:.2f} (Vuln) | y: {likelihood:.2f} (Prob)")

    with tab_trend:
        # SYNTHETIC HISTORICAL DATA (Line Chart)
        # Generate 12 months simulated rainfall trends for this region
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        # Base rainfall modulated by seasonal curve + random
        base_rain = float(defaults.get('Rainfall', 100.0))
        sim_rain = []
        for i in range(12):
            factor = 1.0 + 2.0 * np.exp(-((i - 6)**2)/4) # Peak in July (Month 6)
            sim_rain.append(base_rain * factor * (0.8 + 0.4 * np.random.rand()))
            
        trend_df = pd.DataFrame({"Month": months, "Annual Rainfall (mm)": sim_rain})
        
        fig_line = px.line(trend_df, x="Month", y="Annual Rainfall (mm)", 
                          title=f"Annual Rainfall Trend: {selected_region}",
                          markers=True)
        fig_line.update_traces(line_color='#1f77b4', line_width=3)
        # Highlight current month value? No, just the trend
        st.plotly_chart(fig_line, use_container_width=True)
        
    with tab_dist:
        # HISTOGRAM & DENSITY
        # Distribution of Risk Scores (or Rainfall) across ALL regions in the DB
        st.markdown("#### Regional Risk Distribution")
        
        # Calculate mock risk scores for all regions in DF for comparison
        # Simplified: Use Rainfall as proxy for distribution
        fig_hist = px.histogram(df, x="Rainfall", nbins=20, title="Rainfall Distribution across Regions",
                               opacity=0.7, color_discrete_sequence=['#2ca02c'])
        
        # Add vertical line for current region
        fig_hist.add_vline(x=rainfall, line_dash="dash", line_color="red", annotation_text="Current")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Density Plot (2D Density of Wind vs Pressure)
        fig_dens = px.density_heatmap(df, x="Pressure", y="WindSpeed", title="Wind vs Pressure Density",
                                     color_continuous_scale="Viridis")
        st.plotly_chart(fig_dens, use_container_width=True)

    with tab_corr:
        # SCATTERPLOT
        # Relationship between Infra Index and Rainfall Impact
        fig_scat = px.scatter(df, x="InfrastructureIndex", y="Rainfall", 
                             size="PopulationDensity", color="Region",
                             hover_name="Region", title="Infra Resilience vs Hazard Load")
        
        # Highlight current
        fig_scat.add_trace(go.Scatter(
            x=[infra_index], y=[rainfall],
            mode='markers', marker=dict(color='red', size=20, symbol='star'),
            name=selected_region
        ))
        
        st.plotly_chart(fig_scat, use_container_width=True)


with c2:
    st.markdown("### ✅ Action & Reporting")
    
    # Recommendations
    recs = []
    if current_risk == "High":
        st.error(f"🚨 ACTION: Evacuate {selected_region} Low-Lying Areas.")
        recs = ["Evacuate Low-Lying Areas", "Deploy NDRF Teams", "Secure Power Grids"]
    elif current_risk == "Moderate":
        st.warning("⚠️ ALERT: Pre-position supplies.")
        recs = ["Pre-position Supplies", "Monitor River Levels", "Alert Hospitals"]
    else:
        st.success("✅ STATUS: Routine Monitoring.")
        recs = ["Routine Monitoring"]
        
    for r in recs:
        st.markdown(f"- {r}")

    st.markdown("---")
    
    # DOWNLOADS
    c_d1, c_d2 = st.columns(2)
    with c_d1:
        # CAP PDF
        cap_xml = generate_cap_xml("ai", "Alert", "Desc", "Severe", selected_region, "Met", "Act")
        st.download_button("📡 Download CAP (.xml)", cap_xml, "alert.cap")
    
    with c_d2:
        # SitRep PDF
        pdf_bytes = generate_sitrep(selected_region, current_risk, likelihood, vulnerability, threat, pop_density*5, recs)
        st.download_button(
            label="📄 Download SitRep (.pdf)",
            data=pdf_bytes,
            file_name=f"SitRep_{selected_region}_{datetime.now().date()}.pdf",
            mime="application/pdf"
        )

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey; font-size: 0.8em;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Sources: IMD, NCS, INCOIS, Mock IDRN</div>", unsafe_allow_html=True)
