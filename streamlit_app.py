"""
UrbanSync AI - Master Streamlit Cloud Deployment Dashboard
==========================================================
Autonomous Municipal Synchronization, 3D WebGL Digital Twin,
CVRP Waste Logistics, SILN Mobility & Nirbhaya-Mesh Safety.
"""

from __future__ import annotations

import sys
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
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
    from services.engine_safety.duress_auth import verify_pin
except ImportError:
    verify_pin = None

# Configure Streamlit Page
st.set_page_config(
    page_title="UrbanSync AI | Autonomous Civic Command",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Tech Slate Glassmorphic Styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0b1329 0%, #0d1730 50%, #080d1a 100%);
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .header-card {
        background: rgba(19, 29, 53, 0.9);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 14px;
        padding: 16px 22px;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
    }
    
    .badge-cyan {
        background: rgba(6, 182, 212, 0.18);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.5);
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 800;
        font-family: monospace;
    }

    .badge-live {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 800;
        font-family: monospace;
    }

    .metric-card {
        background: rgba(19, 29, 53, 0.8);
        border: 1px solid rgba(71, 85, 105, 0.8);
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
    }
    
    .metric-title {
        font-size: 11px;
        font-family: monospace;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
    }
    
    .metric-value {
        font-size: 22px;
        font-weight: 900;
        color: #f8fafc;
        margin-top: 3px;
    }

    .metric-sub {
        font-size: 11px;
        color: #38bdf8;
        margin-top: 2px;
    }

    .feed-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Synthetic Lucknow Dataset
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
    {"name": "Gomti Nagar Green Wave", "path": [[80.9462, 26.8467], [80.9600, 26.8510], [80.9800, 26.8563], [80.9980, 26.8530]], "color": [6, 182, 212, 230]},
    {"name": "Charbagh - Hazratganj Corridor", "path": [[80.9180, 26.8320], [80.9320, 26.8400], [80.9462, 26.8467]], "color": [16, 185, 129, 230]},
    {"name": "Aminabad - Chowk Route", "path": [[80.9220, 26.8520], [80.9150, 26.8610], [80.9120, 26.8680]], "color": [244, 63, 94, 230]},
]

LUCKNOW_SAFETY_NODES = [
    {"name": "Pink Booth #1 (Hazratganj)", "lat": 26.8475, "lon": 80.9460, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Pink Booth #2 (Gomti Nagar)", "lat": 26.8550, "lon": 80.9780, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Pink Booth #3 (Aminabad)", "lat": 26.8515, "lon": 80.9230, "type": "Pink Booth", "color": [244, 63, 94]},
    {"name": "Smart CCTV Pole #104", "lat": 26.8490, "lon": 80.9470, "type": "Surveillance Cone", "color": [6, 182, 212]},
    {"name": "Smart CCTV Pole #208", "lat": 26.8580, "lon": 80.9820, "type": "Surveillance Cone", "color": [6, 182, 212]},
]

# -------------------------------------------------------------
# Embedded Standalone 3D WebGL / Three.js Scene HTML
# -------------------------------------------------------------
def get_threejs_scene_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; padding: 0; overflow: hidden; background: #0b1329; font-family: monospace; }
            #canvas-container { width: 100vw; height: 100vh; position: absolute; }
            .hud {
                position: absolute;
                top: 14px;
                left: 14px;
                z-index: 10;
                background: rgba(13, 22, 46, 0.85);
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 10px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 11px;
                pointer-events: none;
                backdrop-filter: blur(8px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }
            .hud-title { font-weight: 800; color: #38bdf8; font-size: 13px; margin-bottom: 4px; }
            .badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; margin-right: 4px; }
            .badge-live { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
            .badge-corridor { background: rgba(6, 182, 212, 0.2); color: #38bdf8; border: 1px solid #06b6d4; }
            .controls-hint {
                position: absolute;
                bottom: 12px;
                right: 14px;
                z-index: 10;
                background: rgba(13, 22, 46, 0.8);
                border: 1px solid rgba(71, 85, 105, 0.6);
                border-radius: 6px;
                padding: 6px 12px;
                color: #94a3b8;
                font-size: 10px;
                pointer-events: none;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div class="hud">
            <div class="hud-title">🏙️ LUCKNOW 3D SPATIAL DIGITAL TWIN</div>
            <div><span class="badge badge-live">● OR-TOOLS CVRP ACTIVE</span> <span class="badge badge-corridor">🚦 GREEN WAVE SYNC</span></div>
            <div style="margin-top: 6px; color: #94a3b8;">Topography: Gomti Waterfront • Hazratganj • Janeshwar Mishra</div>
        </div>
        <div class="controls-hint">Left Drag: Rotate 3D • Right Drag: Pan • Scroll: Zoom</div>
        <div id="canvas-container"></div>

        <script>
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0b1329);
            scene.fog = new THREE.FogExp2(0x0b1329, 0.007);

            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
            camera.position.set(0, 55, 75);

            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2.1;
            controls.minDistance = 15;
            controls.maxDistance = 180;
            controls.target.set(0, 2, 0);

            // Lighting
            const ambient = new THREE.AmbientLight(0x38bdf8, 0.45);
            scene.add(ambient);

            const sun = new THREE.DirectionalLight(0xffffff, 1.4);
            sun.position.set(40, 70, 30);
            sun.castShadow = true;
            scene.add(sun);

            const hemi = new THREE.HemisphereLight(0x38bdf8, 0x0f172a, 0.8);
            scene.add(hemi);

            // Ground plane & Grid
            const groundGeo = new THREE.PlaneGeometry(300, 300);
            const groundMat = new THREE.MeshStandardMaterial({ color: 0x0e172e, roughness: 0.85 });
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            const grid = new THREE.GridHelper(260, 52, 0x1e293b, 0x14203d);
            grid.position.y = 0.05;
            scene.add(grid);

            // Gomti River
            const riverGeo = new THREE.PlaneGeometry(280, 22);
            const riverMat = new THREE.MeshStandardMaterial({
                color: 0x0284c7,
                roughness: 0.1,
                metalness: 0.8,
                emissive: 0x0369a1,
                emissiveIntensity: 0.35,
            });
            const river = new THREE.Mesh(riverGeo, riverMat);
            river.rotation.x = -Math.PI / 2;
            river.rotation.z = -0.32;
            river.position.set(-10, 0.1, -15);
            scene.add(river);

            // 3D Buildings
            const buildingMat = new THREE.MeshStandardMaterial({
                color: 0x1e293b,
                roughness: 0.4,
                metalness: 0.3,
            });
            const buildingHighMat = new THREE.MeshStandardMaterial({
                color: 0x1e293b,
                roughness: 0.2,
                metalness: 0.5,
                emissive: 0x0ea5e9,
                emissiveIntensity: 0.08,
            });

            const buildingCoords = [
                [-35, -20, 10, 18, 12], [-20, -30, 14, 28, 14], [-10, -45, 12, 22, 10],
                [15, -35, 16, 32, 14], [30, -25, 12, 16, 12], [45, -30, 10, 20, 10],
                [-45, 15, 12, 24, 12], [-30, 25, 15, 30, 15], [-15, 35, 12, 18, 12],
                [10, 30, 18, 38, 16], [28, 20, 12, 22, 12], [42, 35, 14, 26, 14],
                [-25, 0, 10, 15, 10], [35, 0, 12, 18, 12], [0, 45, 14, 25, 14]
            ];

            buildingCoords.forEach(([x, z, w, h, d]) => {
                const geo = new THREE.BoxGeometry(w, h, d);
                const mesh = new THREE.Mesh(geo, Math.random() > 0.5 ? buildingHighMat : buildingMat);
                mesh.position.set(x, h / 2, z);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                scene.add(mesh);

                // Add rooftop antenna or beacon
                if (h > 24) {
                    const beaconGeo = new THREE.SphereGeometry(0.6, 8, 8);
                    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e });
                    const beacon = new THREE.Mesh(beaconGeo, beaconMat);
                    beacon.position.set(x, h + 0.8, z);
                    scene.add(beacon);
                }
            });

            // 3D Smart Waste Bins with Elevation Columns & Pulsing Halos
            const bins = [
                { x: 0, z: 5, fill: 0.88, name: "Hazratganj #101" },
                { x: 25, z: -10, fill: 0.92, name: "Gomti Nagar #102" },
                { x: -30, z: -10, fill: 0.78, name: "Aminabad #103" },
                { x: -20, z: 20, fill: 0.95, name: "Charbagh #104" },
                { x: -40, z: 30, fill: 0.65, name: "Chowk #105" },
                { x: 15, z: 15, fill: 0.82, name: "Aliganj #106" },
                { x: 35, z: 20, fill: 0.45, name: "Indiranagar #107" },
            ];

            const halos = [];
            bins.forEach(b => {
                const height = b.fill * 12;
                const colGeo = new THREE.CylinderGeometry(1.6, 1.6, height, 16);
                const color = b.fill > 0.85 ? 0xf43f5e : (b.fill > 0.7 ? 0xf59e0b : 0x10b981);
                const colMat = new THREE.MeshStandardMaterial({
                    color: color,
                    emissive: color,
                    emissiveIntensity: 0.5,
                    roughness: 0.3,
                });
                const colMesh = new THREE.Mesh(colGeo, colMat);
                colMesh.position.set(b.x, height / 2, b.z);
                colMesh.castShadow = true;
                scene.add(colMesh);

                // Pulsing ring at base
                const ringGeo = new THREE.RingGeometry(2.0, 3.2, 24);
                const ringMat = new THREE.MeshBasicMaterial({
                    color: color,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.8,
                });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = -Math.PI / 2;
                ring.position.set(b.x, 0.2, b.z);
                scene.add(ring);
                halos.push(ring);
            });

            // 3D Sweeping CCTV Surveillance Cones
            const cctvNodes = [
                { x: 10, z: 0, rot: 0 },
                { x: -15, z: 12, rot: Math.PI / 3 }
            ];

            const cones = [];
            cctvNodes.forEach(c => {
                const poleGeo = new THREE.CylinderGeometry(0.2, 0.2, 14, 8);
                const poleMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
                const pole = new THREE.Mesh(poleGeo, poleMat);
                pole.position.set(c.x, 7, c.z);
                scene.add(pole);

                const coneGeo = new THREE.ConeGeometry(8, 16, 24, 1, true);
                const coneMat = new THREE.MeshBasicMaterial({
                    color: 0x06b6d4,
                    transparent: true,
                    opacity: 0.3,
                    side: THREE.DoubleSide,
                });
                const cone = new THREE.Mesh(coneGeo, coneMat);
                cone.position.set(c.x, 14, c.z);
                cone.rotation.x = Math.PI / 3;
                scene.add(cone);
                cones.push(cone);
            });

            // Green Wave Corridors (Glowing curved paths)
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(-40, 1, 25),
                new THREE.Vector3(-15, 1, 10),
                new THREE.Vector3(0, 1, 5),
                new THREE.Vector3(25, 1, -8),
                new THREE.Vector3(50, 1, -15),
            ]);
            const tubeGeo = new THREE.TubeGeometry(curve, 40, 0.8, 8, false);
            const tubeMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
            const tube = new THREE.Mesh(tubeGeo, tubeMat);
            scene.add(tube);

            // Animated vehicle moving along the corridor
            const carGeo = new THREE.BoxGeometry(2.4, 1.2, 1.4);
            const carMat = new THREE.MeshStandardMaterial({ color: 0x34d399, emissive: 0x34d399, emissiveIntensity: 0.6 });
            const car = new THREE.Mesh(carGeo, carMat);
            scene.add(car);

            let t = 0;
            function animate() {
                requestAnimationFrame(animate);
                controls.update();

                // Rotate CCTV cones
                cones.forEach((cone, i) => {
                    cone.rotation.y = Math.sin(Date.now() * 0.0012 + i) * 0.8;
                });

                // Pulse halos
                const scale = 1 + Math.sin(Date.now() * 0.004) * 0.25;
                halos.forEach(h => {
                    h.scale.set(scale, scale, 1);
                });

                // Animate vehicle
                t = (t + 0.0025) % 1;
                const pos = curve.getPointAt(t);
                const tangent = curve.getTangentAt(t);
                car.position.copy(pos);
                car.position.y += 0.8;
                car.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), tangent);

                renderer.render(scene, camera);
            }
            animate();

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
        </script>
    </body>
    </html>
    """

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
                <span class="badge-live">● MESH & CAD SYNCED</span>
            </div>
            <p style="margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; font-family: monospace;">
                Autonomous Municipal Synchronization, CVRP Logistics & Nirbhaya-Mesh Safety Twin
            </p>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <a href="https://github.com/Akshat-22-s/URBANSYNC-AI" target="_blank" style="text-decoration: none;">
                <button style="background: rgba(15, 23, 42, 0.8); border: 1px solid #475569; color: #cbd5e1; padding: 7px 14px; border-radius: 8px; font-weight: 700; font-size: 12px; cursor: pointer;">
                    ⭐ GitHub Repo
                </button>
            </a>
            <span style="font-family: monospace; font-size: 12px; color: #38bdf8; font-weight: 700;">
                Lucknow Smart Grid
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
# Main Operational Grid: Left 3D Viewport (70%), Right Cockpit Stack (30%)
# -------------------------------------------------------------
col_viewport, col_cockpit = st.columns([7, 3])

with col_viewport:
    # Mode selector for 3D Spatial Twin
    viewport_mode = st.radio(
        "Viewport Display Mode",
        ["🎮 Interactive 3D WebGL Scene (Three.js Orbit Controls)", "🗺️ 2.5D PyDeck Topography & Street Map"],
        horizontal=True
    )
    
    if "Three.js" in viewport_mode:
        # Render the full interactive WebGL Three.js Scene
        components.html(get_threejs_scene_html(), height=580, scrolling=False)
    else:
        # Render PyDeck Map with CARTO dark basemap (no token needed!)
        df_bins = pd.DataFrame([
            {
                "name": b["name"],
                "lat": b["lat"],
                "lon": b["lon"],
                "elevation": b["fill_pct"] * 15,
                "fill_pct": b["fill_pct"],
                "demand_kg": b["demand_kg"],
                "color": [244, 63, 94, 230] if b["fill_pct"] >= 85 else ([245, 158, 11, 230] if b["fill_pct"] >= 70 else [16, 185, 129, 230]),
            }
            for b in LUCKNOW_BINS
        ])
        
        column_layer = pdk.Layer(
            "ColumnLayer",
            data=df_bins,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=1,
            radius=140,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )
        
        path_layer = pdk.Layer(
            "PathLayer",
            data=pd.DataFrame(LUCKNOW_CORRIDORS),
            get_path="path",
            get_color="color",
            width_scale=25,
            width_min_pixels=4,
            pickable=True,
        )
        
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame(LUCKNOW_SAFETY_NODES),
            get_position=["lon", "lat"],
            get_color="color",
            get_radius=200,
            pickable=True,
            opacity=0.85,
        )
        
        view_state = pdk.ViewState(
            latitude=26.8520,
            longitude=80.9500,
            zoom=12.4,
            pitch=45,
            bearing=15,
        )
        
        # Use CARTO dark basemap - guaranteed to render without any API key!
        st.pydeck_chart(
            pdk.Deck(
                map_provider="carto",
                map_style="dark",
                initial_view_state=view_state,
                layers=[column_layer, path_layer, scatter_layer],
                tooltip={"html": "<b>{name}</b><br/>Fill: {fill_pct}%<br/>Demand: {demand_kg} kg", "style": {"color": "white"}},
            ),
            use_container_width=True
        )

with col_cockpit:
    st.markdown("#### 📡 Real-Time Dispatch Telemetry")
    
    # Real-time scrolling event feed
    events_feed = [
        {"time": "15:42:10", "type": "WASTE_OVERFLOW", "dept": "SANITATION", "color": "#f59e0b", "msg": "Smart Bin #104 (Charbagh) reached 95% volume. Compactor Unit 2 assigned."},
        {"time": "15:40:22", "type": "GREEN_WAVE", "dept": "MOBILITY", "color": "#06b6d4", "msg": "Green corridor active on Gomti Nagar IT Arterial. 4 signals in sync."},
        {"time": "15:38:05", "type": "CAD_SYNC", "dept": "SAFETY", "color": "#10b981", "msg": "UP-112 CAD Police heartbeat verified. 8 Pink Booths nominal."},
        {"time": "15:35:14", "type": "SNATCH_ALERT", "dept": "SAFETY", "color": "#f43f5e", "msg": "Kinematic jerk force >3.2g logged near Aminabad. Surveillance locked."},
    ]
    
    for evt in events_feed:
        st.markdown(f"""
        <div class="feed-card" style="border-left: 4px solid {evt['color']};">
            <div style="display: flex; justify-content: space-between; font-weight: 700;">
                <span style="color: {evt['color']}; font-family: monospace;">{evt['type']}</span>
                <span style="color: #64748b; font-family: monospace;">{evt['time']}</span>
            </div>
            <div style="color: #cbd5e1; margin-top: 4px; line-height: 1.3;">{evt['msg']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### ⏳ Temporal Scrubber")
    time_slider = st.select_slider(
        "Debris Delta State",
        options=["T0: Clean Baseline (08:00)", "T1: Midday Delta (13:30)", "T2: CVRP Flush (17:45)"],
        label_visibility="collapsed"
    )
    if "T0" in time_slider:
        st.caption("🟢 Baseline street geometry active. Homography reference locked.")
    elif "T1" in time_slider:
        st.caption("🟡 Midday debris accumulation detected (+4.8m² cluster).")
    else:
        st.caption("🔵 Active CVRP fleet sweep completed.")

st.markdown("---")

# -------------------------------------------------------------
# Subsystem Interactive Engines (Tabs)
# -------------------------------------------------------------
tab_cvrp, tab_siln, tab_safety, tab_deploy = st.tabs([
    "🚛 Sanitation Core (OR-Tools CVRP Solver)",
    "⚡ SILN Departure Intelligence Engine",
    "🛡️ Nirbhaya-Mesh v3.7 Public Safety",
    "🌐 Deploy Full 100% Next.js Site (Free Vercel Guide)"
])

# =============================================================
# TAB 1: CVRP SOLVER
# =============================================================
with tab_cvrp:
    st.subheader("Autonomous CVRP Fleet Logistics (Google OR-Tools Engine)")
    st.markdown("Solves multi-vehicle garbage compactor routes minimizing travel distance while strictly respecting vehicle payload constraints.")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        num_vehicles = st.slider("Fleet Size (Compactor Trucks)", min_value=1, max_value=4, value=2)
    with col_c2:
        vehicle_capacity = st.number_input("Vehicle Capacity (kg)", min_value=1000, max_value=6000, value=2500, step=500)
    with col_c3:
        depot_select = st.selectbox("Municipal Depot Location", [LUCKNOW_DEPOT["name"]])
        
    if st.button("⚡ Solve Optimal Multi-Vehicle Route", type="primary"):
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
                for r in result.routes:
                    with st.expander(f"🚛 Vehicle #{r.vehicle_id + 1} — Load: {r.total_load_kg} / {vehicle_capacity} kg ({r.distance_km:.2f} km)"):
                        route_steps = []
                        for idx in r.node_indices:
                            node = solver_nodes[idx]
                            route_steps.append({
                                "Stop #": len(route_steps) + 1,
                                "Location": node.get("name", f"Node {idx}"),
                                "Demand (kg)": node.get("demand_kg", 0),
                                "Fill %": node.get("fill_pct", 0)
                            })
                        st.table(pd.DataFrame(route_steps))
            except Exception as ex:
                st.error(f"Solver Error: {ex}")
        else:
            st.info("Synthetic Route Computed: 2 Trucks dispatched. Total Distance: 24.6 km.")

# =============================================================
# TAB 2: SILN DEPARTURE INTELLIGENCE
# =============================================================
with tab_siln:
    st.subheader("SILN / LogPose Mobility Engine — Departure Intelligence")
    st.latex(r"T_{\text{depart}} = T_{\text{arrive}} - D_{\text{transit}} - B_{\text{dynamic}}")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        target_event_time = st.time_input("Target Arrival Time", datetime.strptime("18:30", "%H:%M").time())
        transit_duration = st.slider("Transit Duration (minutes)", min_value=5, max_value=90, value=35)
    with col_s2:
        st.markdown("**Dynamic Buffer Penalties (minutes)**")
        b_parking = st.slider("🅿️ Parking Search Delay", min_value=0, max_value=25, value=8)
        b_toll = st.slider("🛣️ Toll Queue Delay", min_value=0, max_value=20, value=4)
        b_weather = st.slider("🌧️ Weather / Road Degradation", min_value=0, max_value=30, value=6)
        
    total_buffer = b_parking + b_toll + b_weather
    event_dt = datetime.combine(datetime.today(), target_event_time)
    arrive_by = event_dt - timedelta(minutes=5)
    depart_at = arrive_by - timedelta(minutes=(transit_duration + total_buffer))
    
    st.markdown(f"""
    <div style="background: rgba(19, 29, 53, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 12px; padding: 20px; margin-top: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="font-family: monospace; font-size: 12px; color: #94a3b8;">CALCULATED DEPARTURE TIME</span>
                <div style="font-size: 34px; font-weight: 900; color: #38bdf8; font-family: monospace;">
                    {depart_at.strftime('%H:%M:%S')}
                </div>
                <div style="color: #cbd5e1; font-size: 13px; margin-top: 4px;">
                    Arrive at destination by: <b>{arrive_by.strftime('%H:%M')}</b> (5 min safety margin before event)
                </div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 12px; color: #94a3b8;">Dynamic Buffer Breakdown:</span>
                <div style="font-size: 18px; font-weight: 800; color: #34d399; font-family: monospace; margin-top: 4px;">
                    +{total_buffer} min total
                </div>
                <span style="font-size: 11px; color: #64748b;">Parking: +{b_parking}m • Toll: +{b_toll}m • Weather: +{b_weather}m</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================
# TAB 3: NIRBHAYA-MESH SAFETY
# =============================================================
with tab_safety:
    st.subheader("Nirbhaya-Mesh v3.7 Public Safety Engine")
    
    col_d1, col_d2 = st.columns(2)
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
# TAB 4: VERCEL DEPLOYMENT GUIDE (For the 100% Next.js Site)
# =============================================================
with tab_deploy:
    st.subheader("🚀 Deploy the Full Next.js 3D Cockpit to the Web (100% Free on Vercel)")
    st.markdown("""
    Aapka repository **Next.js + Three.js** frontend include karta hai jo localhost:3000 par chalta hai. 
    Next.js ko direct internet par live karne ke liye **Vercel** sabse best aur fast platform hai (1-click free hosting).
    
    #### 3 Simple Steps to Deploy:
    1. **Vercel par Jayein:** [vercel.com](https://vercel.com) open karein aur **"Sign Up with GitHub"** karein.
    2. **Import Repository:** 
       - "Add New Project" select karein.
       - Apna GitHub repo **`Akshat-22-s/URBANSYNC-AI`** choose karein.
    3. **Configure Project:**
       - **Root Directory** ko click karein aur **`client`** select karein (kyunki Next.js app `client/` folder mein hai).
       - Framework Preset automatic `Next.js` detect ho jayega.
       - **Deploy** button click karein!
       
    ✨ **Result:** 1 minute ke andar aapki full Next.js 3D Spatial Digital Twin website public URL par live ho jayegi (e.g. `https://urbansync-ai.vercel.app`)!
    """)

# -------------------------------------------------------------
# Footer
# -------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 12px; font-family: monospace;">
    UrbanSync AI v4.0 Meta-Build • Lucknow Municipal Synchronization Grid • Powered by Streamlit, Three.js, OR-Tools & UP-112 CAD
</div>
""", unsafe_allow_html=True)
