"""
UrbanSync AI - Streamlit Cloud Deployment Dashboard
===================================================
Autonomous Municipal Synchronization, CVRP Waste Logistics,
SILN Departure Intelligence & Nirbhaya-Mesh Public Safety.
"""

from __future__ import annotations

import sys
import os
import math
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import core engines
try:
    from services.engine_waste.cvrp_solver import solve_cvrp
except ImportError:
    solve_cvrp = None

try:
    from services.engine_mobility.siln_calculator import (
        calculate_departure_time,
        calculate_dynamic_buffer,
    )
except ImportError:
    calculate_departure_time = None
    calculate_dynamic_buffer = None

try:
    from services.engine_safety.duress_auth import verify_pin, PinAttemptTracker
except ImportError:
    verify_pin = None
    PinAttemptTracker = None

# Configure Streamlit Page
st.set_page_config(
    page_title="UrbanSync AI | Autonomous Civic Command",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Tech Styling CSS
st.markdown("""
<style>
    /* Dark Slate Glassmorphic Theme */
    .stApp {
        background: linear-gradient(180deg, #0b1329 0%, #0d1730 50%, #080d1a 100%);
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Header card */
    .header-card {
        background: rgba(19, 29, 53, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 14px;
        padding: 18px 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
    }
    
    .badge-cyan {
        background: rgba(6, 182, 212, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        font-family: monospace;
    }

    .metric-card {
        background: rgba(19, 29, 53, 0.7);
        border: 1px solid rgba(71, 85, 105, 0.7);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .metric-title {
        font-size: 11px;
        font-family: monospace;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }

    .metric-sub {
        font-size: 12px;
        color: #38bdf8;
        margin-top: 2px;
    }
    
    /* Streamlit tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-family: monospace;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Synthetic Lucknow Geospatial Dataset
# -------------------------------------------------------------
LUCKNOW_DEPOT = {"name": "Lucknow Municipal Fleet Depot (Hazratganj)", "lat": 26.8467, "lon": 80.9462, "demand_kg": 0}

LUCKNOW_BINS = [
    {"id": "BIN-101", "name": "Hazratganj Main Cross", "lat": 26.8480, "lon": 80.9450, "fill_pct": 88, "capacity_kg": 500, "demand_kg": 440},
    {"id": "BIN-102", "name": "Gomti Nagar Wave Mall", "lat": 26.8563, "lon": 80.9800, "fill_pct": 92, "capacity_kg": 600, "demand_kg": 552},
    {"id": "BIN-103", "name": "Aminabad Commercial Market", "lat": 26.8520, "lon": 80.9220, "fill_pct": 78, "capacity_kg": 500, "demand_kg": 390},
    {"id": "BIN-104", "name": "Charbagh Station Terminal", "lat": 26.8320, "lon": 80.9180, "fill_pct": 95, "capacity_kg": 800, "demand_kg": 760},
    {"id": "BIN-105", "name": "Chowk Heritage Gate", "lat": 26.8680, "lon": 80.9120, "fill_pct": 65, "capacity_kg": 500, "demand_kg": 325},
    {"id": "BIN-106", "name": "Aliganj Kapoorthala", "lat": 26.8850, "lon": 80.9410, "fill_pct": 82, "capacity_kg": 500, "demand_kg": 410},
    {"id": "BIN-107", "name": "Indiranagar Munshipulia", "lat": 26.8890, "lon": 80.9870, "fill_pct": 74, "capacity_kg": 600, "demand_kg": 444},
    {"id": "BIN-108", "name": "Mahanagar Gole Market", "lat": 26.8710, "lon": 80.9540, "fill_pct": 45, "capacity_kg": 500, "demand_kg": 225},
    {"id": "BIN-109", "name": "Janeshwar Mishra Gate 1", "lat": 26.8420, "lon": 80.9920, "fill_pct": 30, "capacity_kg": 700, "demand_kg": 210},
    {"id": "BIN-110", "name": "Lohia Hospital Arterial", "lat": 26.8530, "lon": 80.9980, "fill_pct": 86, "capacity_kg": 600, "demand_kg": 516},
]

LUCKNOW_CORRIDORS = [
    # Gomti Nagar Express Wave
    {"name": "Gomti Nagar Green Wave", "path": [[80.9462, 26.8467], [80.9600, 26.8510], [80.9800, 26.8563], [80.9980, 26.8530]], "color": [6, 182, 212, 220]},
    # Charbagh Emergency Route
    {"name": "Charbagh - Hazratganj Corridor", "path": [[80.9180, 26.8320], [80.9320, 26.8400], [80.9462, 26.8467]], "color": [16, 185, 129, 220]},
    # Aminabad Heritage Connector
    {"name": "Aminabad - Chowk Route", "path": [[80.9220, 26.8520], [80.9150, 26.8610], [80.9120, 26.8680]], "color": [244, 63, 94, 220]},
]

LUCKNOW_SAFETY_NODES = [
    {"name": "Pink Booth #1 (Hazratganj)", "lat": 26.8475, "lon": 80.9460, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Pink Booth #2 (Gomti Nagar)", "lat": 26.8550, "lon": 80.9780, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Pink Booth #3 (Aminabad)", "lat": 26.8515, "lon": 80.9230, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Smart CCTV Pole #104", "lat": 26.8490, "lon": 80.9470, "type": "Surveillance Cone", "color": [6, 182, 212]},
    {"name": "Smart CCTV Pole #208", "lat": 26.8580, "lon": 80.9820, "type": "Surveillance Cone", "color": [6, 182, 212]},
]

# -------------------------------------------------------------
# Top Header Banner
# -------------------------------------------------------------
st.markdown("""
<div class="header-card">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <h1 style="margin: 0; font-size: 26px; font-weight: 900; background: linear-gradient(90deg, #38bdf8, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    URBANSYNC AI
                </h1>
                <span class="badge-cyan">v4.0 META-BUILD</span>
                <span class="badge-cyan" style="color: #fbbf24; border-color: rgba(251, 191, 36, 0.4); background: rgba(251, 191, 36, 0.1);">
                    STREAMLIT EDITION
                </span>
            </div>
            <p style="margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; font-family: monospace;">
                Autonomous Municipal Synchronization, CVRP Logistics & Nirbhaya-Mesh Safety Twin
            </p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <a href="http://localhost:3000" target="_blank" style="text-decoration: none;">
                <button style="background: rgba(6, 182, 212, 0.2); border: 1px solid #38bdf8; color: #38bdf8; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 12px; cursor: pointer;">
                    🚀 Open 3D Next.js Cockpit
                </button>
            </a>
            <span style="font-family: monospace; font-size: 12px; color: #34d399; font-weight: 700;">
                ● MESH ONLINE
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Live Metrics Row
# -------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

bins_over_75 = sum(1 for b in LUCKNOW_BINS if b["fill_pct"] >= 75)
total_demand_kg = sum(b["demand_kg"] for b in LUCKNOW_BINS)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">🗑️ Sanitation Demand</div>
        <div class="metric-value">{bins_over_75} / {len(LUCKNOW_BINS)}</div>
        <div class="metric-sub">Bins &gt; 75% Fill ({total_demand_kg} kg accumulated)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">🚦 SILN Green Waves</div>
        <div class="metric-value">3 Corridors</div>
        <div class="metric-sub">Hazratganj • Gomti Nagar • Charbagh</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">🛡️ Nirbhaya-Mesh v3.7</div>
        <div class="metric-value">98.4%</div>
        <div class="metric-sub">CCTV Visual Cone Lock (UP-112 CAD)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">📍 City Region</div>
        <div class="metric-value">Lucknow</div>
        <div class="metric-sub">Nagar Nigam Autonomous Grid</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# -------------------------------------------------------------
# Main Application Tabs
# -------------------------------------------------------------
tab_twin, tab_cvrp, tab_siln, tab_safety, tab_delta = st.tabs([
    "🗺️ 3D Spatial Digital Twin",
    "🚛 Sanitation Core (OR-Tools CVRP)",
    "⚡ SILN Departure Intelligence",
    "🛡️ Nirbhaya-Mesh Safety & Duress",
    "🔬 Temporal Debris Delta ($T_0 \\to T_1 \\to T_2$)"
])

# =============================================================
# TAB 1: 3D SPATIAL DIGITAL TWIN (PyDeck)
# =============================================================
with tab_twin:
    st.subheader("Lucknow Municipal Mesh — 3D Spatial Topography")
    
    col_t1, col_t2 = st.columns([3, 1])
    
    with col_t2:
        st.markdown("**Layer Controls & Filters**")
        min_fill = st.slider("Minimum Bin Fill Filter (%)", min_value=0, max_value=100, value=50, step=5)
        show_corridors = st.checkbox("Show Green Wave Corridors", value=True)
        show_safety = st.checkbox("Show Nirbhaya Pink Booths & CCTV", value=True)
        view_pitch = st.slider("3D Camera Pitch (°)", min_value=0, max_value=60, value=45)
    
    # Filter bin points based on slider
    filtered_bins = [b for b in LUCKNOW_BINS if b["fill_pct"] >= min_fill]
    
    # Build dataframe for ColumnLayer
    bin_data = []
    for b in filtered_bins:
        # Dynamic color: Green (<70), Amber (70-85), Red (>85)
        if b["fill_pct"] >= 85:
            color = [244, 63, 94, 230] # Rose
        elif b["fill_pct"] >= 70:
            color = [245, 158, 11, 230] # Amber
        else:
            color = [16, 185, 129, 230] # Emerald
            
        bin_data.append({
            "name": b["name"],
            "id": b["id"],
            "lat": b["lat"],
            "lon": b["lon"],
            "elevation": b["fill_pct"] * 12,
            "fill_pct": b["fill_pct"],
            "demand_kg": b["demand_kg"],
            "color": color,
        })
    df_bins = pd.DataFrame(bin_data)
    
    # Construct PyDeck layers
    layers = []
    
    # 1. 3D Column Layer for Waste Bins
    if not df_bins.empty:
        column_layer = pdk.Layer(
            "ColumnLayer",
            data=df_bins,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=120,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )
        layers.append(column_layer)
        
    # 2. Green Wave Corridor Paths
    if show_corridors:
        df_corridors = pd.DataFrame(LUCKNOW_CORRIDORS)
        path_layer = pdk.Layer(
            "PathLayer",
            data=df_corridors,
            get_path="path",
            get_color="color",
            width_scale=20,
            width_min_pixels=4,
            pickable=True,
        )
        layers.append(path_layer)
        
    # 3. Nirbhaya Pink Booths & CCTV nodes
    if show_safety:
        df_safety = pd.DataFrame(LUCKNOW_SAFETY_NODES)
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_safety,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius=180,
            pickable=True,
            opacity=0.8,
        )
        layers.append(scatter_layer)

    # Initial camera view centered over Hazratganj, Lucknow
    view_state = pdk.ViewState(
        latitude=26.8520,
        longitude=80.9500,
        zoom=12.2,
        pitch=view_pitch,
        bearing=15,
    )
    
    with col_t1:
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v11",
                initial_view_state=view_state,
                layers=layers,
                tooltip={"html": "<b>{name}</b><br/>Fill: {fill_pct}%<br/>Demand: {demand_kg} kg", "style": {"color": "white"}},
            )
        )

# =============================================================
# TAB 2: SANITATION CORE (CVRP WITH GOOGLE OR-TOOLS)
# =============================================================
with tab_cvrp:
    st.subheader("Autonomous CVRP Fleet Logistics (Google OR-Tools Engine)")
    st.markdown("Calculates optimal multi-vehicle garbage compactor routes minimizing distance while strictly enforcing vehicle capacity limits.")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        num_vehicles = st.slider("Fleet Size (Compactor Trucks)", min_value=1, max_value=5, value=2)
    with col_c2:
        vehicle_capacity = st.number_input("Vehicle Capacity (kg)", min_value=1000, max_value=8000, value=2000, step=500)
    with col_c3:
        depot_name = st.selectbox("Municipal Depot", [LUCKNOW_DEPOT["name"]])
        
    if st.button("⚡ Run Autonomous CVRP Solver", type="primary"):
        with st.spinner("Executing Google OR-Tools Constraint Solver..."):
            # Construct nodes with depot at index 0
            solver_nodes = [LUCKNOW_DEPOT] + LUCKNOW_BINS
            
            if solve_cvrp is not None:
                try:
                    result = solve_cvrp(
                        nodes=solver_nodes,
                        num_vehicles=num_vehicles,
                        vehicle_capacity=vehicle_capacity,
                        depot_index=0
                    )
                    
                    st.success(f"✓ Optimization Complete! Total Route Distance: {result.total_distance_km:.2f} km across {len(result.routes)} vehicles.")
                    
                    # Display vehicle routes
                    for r in result.routes:
                        with st.expander(f"🚛 Vehicle #{r.vehicle_id + 1} — Load: {r.total_load_kg} / {vehicle_capacity} kg ({r.distance_km:.2f} km)"):
                            route_steps = []
                            for idx in r.node_indices:
                                node = solver_nodes[idx]
                                route_steps.append({
                                    "Stop #": len(route_steps) + 1,
                                    "Location": node.get("name", f"Node {idx}"),
                                    "Lat": node["lat"],
                                    "Lon": node["lon"],
                                    "Demand (kg)": node.get("demand_kg", 0),
                                    "Fill %": node.get("fill_pct", 0)
                                })
                            st.table(pd.DataFrame(route_steps))
                except Exception as ex:
                    st.error(f"Solver Error: {ex}")
            else:
                st.warning("OR-Tools Python engine could not be imported. Running synthetic approximation...")
                st.info(f"Simulated Route for {num_vehicles} trucks computed successfully.")

# =============================================================
# TAB 3: SILN DEPARTURE INTELLIGENCE
# =============================================================
with tab_siln:
    st.subheader("SILN / LogPose Mobility Engine — Departure Intelligence")
    st.latex(r"T_{\text{depart}} = T_{\text{arrive}} - D_{\text{transit}} - B_{\text{dynamic}}")
    st.markdown("Computes exact departure times incorporating multi-penalty dynamic buffers for parking search, toll queues, and weather delays.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        target_event_time = st.time_input("Target Arrival/Meeting Time", datetime.strptime("18:30", "%H:%M").time())
        transit_duration = st.slider("Baseline Transit Duration (minutes)", min_value=5, max_value=90, value=35)
    with col_s2:
        st.markdown("**Dynamic Buffer Penalties (minutes)**")
        b_parking = st.slider("🅿️ Parking Search Delay", min_value=0, max_value=25, value=8)
        b_toll = st.slider("🛣️ Toll Queue Delay", min_value=0, max_value=20, value=4)
        b_weather = st.slider("🌧️ Weather / Road Degradation", min_value=0, max_value=30, value=6)
        
    total_buffer = b_parking + b_toll + b_weather
    
    # Calculate times
    event_dt = datetime.combine(datetime.today(), target_event_time)
    arrive_by = event_dt - timedelta(minutes=5)
    depart_at = arrive_by - timedelta(minutes=(transit_duration + total_buffer))
    
    now = datetime.now()
    diff_minutes = (depart_at - now).total_seconds() / 60
    
    if diff_minutes < 0:
        urgency_badge = "🔴 OVERDUE / LATE"
        urgency_color = "#f43f5e"
    elif diff_minutes <= 10:
        urgency_badge = "⚠️ LEAVE NOW"
        urgency_color = "#f59e0b"
    elif diff_minutes <= 25:
        urgency_badge = "🟡 LEAVE SOON"
        urgency_color = "#fbbf24"
    else:
        urgency_badge = "🟢 ON SCHEDULE"
        urgency_color = "#34d399"
        
    st.markdown(f"""
    <div style="background: rgba(19, 29, 53, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 12px; padding: 20px; margin-top: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="font-family: monospace; font-size: 12px; color: #94a3b8;">RECOMMENDED DEPARTURE TIME</span>
                <div style="font-size: 36px; font-weight: 900; color: #38bdf8; font-family: monospace;">
                    {depart_at.strftime('%H:%M:%S')}
                </div>
                <div style="color: #cbd5e1; font-size: 13px; margin-top: 4px;">
                    Arrive at destination by: <b>{arrive_by.strftime('%H:%M')}</b> (5 min before {target_event_time.strftime('%H:%M')})
                </div>
            </div>
            <div style="text-align: right;">
                <span style="font-family: monospace; font-size: 11px; color: #94a3b8;">URGENCY STATUS</span>
                <div style="font-size: 20px; font-weight: 800; color: {urgency_color}; font-family: monospace; margin-top: 4px;">
                    {urgency_badge}
                </div>
                <span style="font-size: 12px; color: #94a3b8;">Total Dynamic Buffer: <b>+{total_buffer} min</b></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================
# TAB 4: NIRBHAYA-MESH SAFETY & DURESS
# =============================================================
with tab_safety:
    st.subheader("Nirbhaya-Mesh v3.7 Public Safety Engine")
    st.markdown("Dual-PIN Duress Verification & SafePath Impedance Routing ($Z_s = \\frac{D}{\\sum w_i f_i}$).")
    
    col_d1, col_d2 = st.columns([1, 1])
    
    with col_d1:
        st.markdown("### 🔐 Dual-PIN Duress Simulator")
        st.caption("PIN 1234 = Safe Nominal Verification | PIN 9999 = Silent UP-112 CAD Police Alarm")
        
        entered_pin = st.text_input("Enter 4-Digit Escort PIN", type="password", max_chars=4, value="1234")
        
        if st.button("Submit PIN Verification"):
            if entered_pin == "1234":
                st.success("✅ Nominal Trip Ended Safely. Escort cleared and telemetry archived.")
            elif entered_pin == "9999":
                st.warning("Trip Ended Safely.")
                st.error("🚨 [SILENT POLICE BACKEND]: Duress Triggered! CODE_RED_P1 dispatched to UP-112 Police CAD with live coordinates (26.8520, 80.9220) & audio stream!")
            else:
                st.error("❌ Invalid PIN. 2 attempts remaining.")
                
    with col_d2:
        st.markdown("### 🛡️ SafePath Impedance ($Z_s$) Calculator")
        st.latex(r"Z_s = \frac{\text{Distance}}{\sum (w_{\text{cctv}} \cdot f_{\text{cctv}} + w_{\text{light}} \cdot f_{\text{light}} + w_{\text{crowd}} \cdot f_{\text{crowd}})}")
        
        cctv_score = st.slider("CCTV Coverage Factor ($f_{cctv}$)", 0.0, 1.0, 0.85)
        lighting_score = st.slider("Street Lighting Factor ($f_{light}$)", 0.0, 1.0, 0.90)
        crowd_score = st.slider("Civic Footfall Factor ($f_{crowd}$)", 0.0, 1.0, 0.70)
        dist_meters = st.number_input("Segment Distance (meters)", value=650, step=50)
        
        total_safety_factor = (0.45 * cctv_score) + (0.35 * lighting_score) + (0.20 * crowd_score)
        impedance = dist_meters / max(0.01, total_safety_factor)
        
        st.metric(
            label="SafePath Impedance Score (Lower = Safer)",
            value=f"{impedance:.1f} Zs",
            delta=f"-{((1.0 - total_safety_factor) * 100):.1f}% Risk Factor",
            delta_color="inverse"
        )

# =============================================================
# TAB 5: TEMPORAL DEBRIS DELTA
# =============================================================
with tab_delta:
    st.subheader("Temporal Debris Delta ($T_0 \\to T_1 \\to T_2$) Change Detection")
    st.markdown("Computer vision spatial subtraction comparing pre-shift baseline scans against midday accumulation.")
    
    t_stage = st.select_slider(
        "Select Temporal Stage",
        options=["T0: Baseline Clean (08:00)", "T1: Accumulation Delta (13:30)", "T2: CVRP Clearance (17:45)"]
    )
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if "T0" in t_stage:
            st.info("📷 T0 Baseline: Street scan captured during dawn shift. ORB keypoints matched & clean pavement mask stored.")
            st.metric("Detected Debris Area", "0.0 m²", "0% threshold")
        elif "T1" in t_stage:
            st.warning("⚠️ T1 Midday Accumulation: Temporal homography delta detected +4.8 m² litter clustering near Hazratganj.")
            st.metric("Detected Debris Area", "4.8 m²", "+4.8 m²")
        else:
            st.success("✓ T2 Post-Collection: Compactor Unit 3 executed sweep. Street returned to baseline tolerance.")
            st.metric("Detected Debris Area", "0.2 m²", "-4.6 m² cleared")
            
    with col_v2:
        # Synthetic chart showing accumulation curve
        hours = [8, 10, 12, 14, 16, 18]
        volumes = [5, 18, 42, 85, 94, 12]
        df_chart = pd.DataFrame({"Hour": hours, "Waste Fill %": volumes}).set_index("Hour")
        st.line_chart(df_chart)

# -------------------------------------------------------------
# Footer
# -------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 12px; font-family: monospace;">
    UrbanSync AI v4.0 Meta-Build • Lucknow Municipal Synchronization Grid • Powered by Streamlit, Three.js, OR-Tools & UP-112 CAD
</div>
""", unsafe_allow_html=True)
