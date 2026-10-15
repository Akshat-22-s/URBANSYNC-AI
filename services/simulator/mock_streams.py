"""
UrbanSync AI - Mock Data Streams Generator
==========================================
Provides realistic mock telemetry data generators for simulated citizen kinematics,
smart waste bin capacity accumulation, sudden high-G snatch alerts,
emergency vehicle dispatches, and green wave corridor synchronization.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np


# Lucknow reference center and landmark coordinates
LUCKNOW_LANDMARKS = [
    {"name": "Hazratganj Chauraha", "lat": 26.8467, "lon": 80.9462},
    {"name": "Vidhan Sabha Marg", "lat": 26.8428, "lon": 80.9405},
    {"name": "Charbagh Railway Station", "lat": 26.8322, "lon": 80.9197},
    {"name": "Aminabad Central Market", "lat": 26.8450, "lon": 80.9250},
    {"name": "Chowk Heritage Zone", "lat": 26.8665, "lon": 80.9042},
    {"name": "1090 Women Power Line", "lat": 26.8480, "lon": 80.9670},
    {"name": "Patrakarpuram Gomti Nagar", "lat": 26.8563, "lon": 80.9800},
    {"name": "Vibhuti Khand IT Hub", "lat": 26.8640, "lon": 81.0020},
    {"name": "Polytechnic Chauraha", "lat": 26.8711, "lon": 80.9984},
    {"name": "Indira Nagar Chauraha", "lat": 26.8785, "lon": 80.9902},
    {"name": "Aliganj Purania", "lat": 26.8833, "lon": 80.9392},
    {"name": "Mahanagar Gole Market", "lat": 26.8742, "lon": 80.9472},
    {"name": "Alambagh Bus Terminal", "lat": 26.8166, "lon": 80.9022},
    {"name": "Dr. RML Hospital", "lat": 26.8610, "lon": 80.9890},
    {"name": "KD Singh Babu Stadium", "lat": 26.8530, "lon": 80.9400},
]


def get_initial_citizens(n: int = 50) -> List[Dict[str, Any]]:
    """
    Initialize positions and states for simulated citizens around Lucknow.

    Parameters
    ----------
    n : int, optional
        Number of citizens to initialize (default is 50).

    Returns
    -------
    list of dict
        List of initialized citizen records.
    """
    citizens: List[Dict[str, Any]] = []
    base_lat = 26.8467
    base_lon = 80.9462

    statuses = ["pedestrian", "cyclist", "transit_rider", "stationary"]
    status_weights = [0.55, 0.20, 0.15, 0.10]

    for i in range(n):
        landmark = LUCKNOW_LANDMARKS[i % len(LUCKNOW_LANDMARKS)]
        lat_jitter = float(np.random.normal(0, 0.012))
        lon_jitter = float(np.random.normal(0, 0.012))

        lat = round(landmark["lat"] + lat_jitter, 6)
        lon = round(landmark["lon"] + lon_jitter, 6)
        heading = round(float(np.random.uniform(0.0, 360.0)), 1)
        speed = round(float(np.random.uniform(0.8, 2.5)), 2)
        status = str(np.random.choice(statuses, p=status_weights))

        citizens.append({
            "citizen_id": f"cit_{i + 1:03d}",
            "device_id": f"dev_{uuid.uuid4().hex[:6]}",
            "lat": lat,
            "lon": lon,
            "base_lat": lat,
            "base_lon": lon,
            "heading": heading,
            "speed_mps": speed,
            "status": status,
            "battery_pct": int(np.random.randint(45, 100)),
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    return citizens


def generate_citizen_packet(citizen_id: str, base_lat: float, base_lon: float) -> Dict[str, Any]:
    """
    Generate next kinematic telemetry packet for a citizen undergoing random walk.

    Parameters
    ----------
    citizen_id : str
        Unique citizen identifier.
    base_lat : float
        Current latitude of the citizen.
    base_lon : float
        Current longitude of the citizen.

    Returns
    -------
    dict
        Kinematic packet with updated latitude, longitude, heading, speed, and normal accel.
    """
    # Small jitter in lat/lon (~10-15 meters)
    d_lat = float(np.random.normal(0.0, 0.00012))
    d_lon = float(np.random.normal(0.0, 0.00012))

    new_lat = round(base_lat + d_lat, 6)
    new_lon = round(base_lon + d_lon, 6)

    # Heading in degrees [0, 360)
    angle_rad = math.atan2(d_lat, d_lon)
    heading = round((math.degrees(angle_rad) + 360.0) % 360.0, 1)

    # Walking speed in m/s with normal noise
    speed_mps = round(float(np.clip(np.random.normal(1.35, 0.35), 0.2, 4.0)), 2)

    # Normal acceleration in g's (nominal movement < 0.35 g)
    accel_g = round(float(np.clip(np.random.normal(0.08, 0.03), 0.02, 0.35)), 3)

    return {
        "telemetry_type": "citizen_kinematics",
        "citizen_id": citizen_id,
        "lat": new_lat,
        "lon": new_lon,
        "heading": heading,
        "speed_mps": speed_mps,
        "accel_g": accel_g,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_initial_bins(n: int = 30) -> List[Dict[str, Any]]:
    """
    Initialize municipal waste bin locations and fill levels across Lucknow.

    Parameters
    ----------
    n : int, optional
        Number of waste bins to initialize (default is 30).

    Returns
    -------
    list of dict
        List of initialized waste bin states.
    """
    bins: List[Dict[str, Any]] = []
    waste_types = ["general", "recyclable", "organic"]
    capacities = [240, 660, 1100]

    for i in range(n):
        landmark = LUCKNOW_LANDMARKS[i % len(LUCKNOW_LANDMARKS)]
        lat_offset = float(np.random.uniform(-0.008, 0.008))
        lon_offset = float(np.random.uniform(-0.008, 0.008))

        lat = round(landmark["lat"] + lat_offset, 6)
        lon = round(landmark["lon"] + lon_offset, 6)
        capacity = int(np.random.choice(capacities))
        initial_fill = round(float(np.random.uniform(20.0, 65.0)), 1)
        wtype = str(np.random.choice(waste_types, p=[0.5, 0.3, 0.2]))

        bins.append({
            "bin_id": f"bin_{i + 1:03d}",
            "location_name": f"{landmark['name']} Sector {chr(65 + (i % 6))}",
            "lat": lat,
            "lon": lon,
            "capacity_liters": capacity,
            "current_fill_pct": initial_fill,
            "waste_type": wtype,
            "battery_pct": int(np.random.randint(65, 100)),
            "last_emptied": datetime.now(timezone.utc).isoformat()
        })

    return bins


def generate_waste_update(bin_id: str, current_fill: float) -> Dict[str, Any]:
    """
    Simulate municipal waste bin accumulation using a Poisson increment process.

    Parameters
    ----------
    bin_id : str
        Waste bin identifier.
    current_fill : float
        Current fill percentage (0.0 to 100.0).

    Returns
    -------
    dict
        Waste update delta packet with status and fill metrics.
    """
    # Poisson event generation for waste deposit events
    deposit_count = int(np.random.poisson(lam=2.5))
    delta_fill = round(deposit_count * float(np.random.uniform(0.6, 1.4)), 1)

    new_fill = round(min(100.0, max(0.0, float(current_fill) + delta_fill)), 1)

    if new_fill >= 85.0:
        status = "CRITICAL"
        requires_dispatch = True
    elif new_fill >= 70.0:
        status = "WARNING"
        requires_dispatch = False
    else:
        status = "NORMAL"
        requires_dispatch = False

    return {
        "telemetry_type": "waste_bin_delta",
        "bin_id": bin_id,
        "previous_fill_pct": round(float(current_fill), 1),
        "delta_fill_pct": round(float(new_fill - current_fill), 1),
        "current_fill_pct": new_fill,
        "status": status,
        "requires_dispatch": requires_dispatch,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def generate_snatch_event(citizen_id: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    Generate an anomalous high-G jerk snatch/fall detection alert.
    Requires accel_g > 3.0 according to system specification.

    Parameters
    ----------
    citizen_id : str
        Citizen ID experiencing the anomalous jerk.
    lat : float
        Latitude where anomaly occurred.
    lon : float
        Longitude where anomaly occurred.

    Returns
    -------
    dict
        High-priority safety alert packet.
    """
    # Acceleration in g's strictly exceeding 3.0 g threshold
    accel_g = round(float(np.random.uniform(3.4, 5.8)), 2)
    jerk_g_per_sec = round(float(np.random.uniform(9.5, 18.2)), 2)
    confidence = round(float(np.random.uniform(0.92, 0.99)), 2)
    alert_id = f"alert_snatch_{uuid.uuid4().hex[:8]}"

    return {
        "alert_id": alert_id,
        "event_type": "SNATCH_DETECTED",
        "citizen_id": citizen_id,
        "lat": round(float(lat), 6),
        "lon": round(float(lon), 6),
        "accel_g": accel_g,
        "jerk_g_per_sec": jerk_g_per_sec,
        "confidence": confidence,
        "severity": "CRITICAL",
        "action_recommended": "DISPATCH_NEAREST_PATROL",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def generate_dispatch_event() -> Dict[str, Any]:
    """
    Generate a mock emergency service vehicle dispatch record.

    Returns
    -------
    dict
        Emergency dispatch packet with route, unit ID, and ETA.
    """
    unit_types = ["PCR_VAN", "PINK_PATROL_SCOOTER", "AMBULANCE", "TRAFFIC_INTERCEPTOR"]
    unit_type = str(np.random.choice(unit_types))

    origin_landmark = LUCKNOW_LANDMARKS[int(np.random.randint(0, len(LUCKNOW_LANDMARKS)))]
    dest_landmark = LUCKNOW_LANDMARKS[int(np.random.randint(0, len(LUCKNOW_LANDMARKS)))]

    eta_min = round(float(np.random.uniform(3.0, 9.5)), 1)
    speed_kmh = round(float(np.random.uniform(38.0, 68.0)), 1)

    return {
        "telemetry_type": "emergency_dispatch",
        "dispatch_id": f"disp_{uuid.uuid4().hex[:8]}",
        "unit_id": f"UP32_{unit_type[:3]}_{np.random.randint(100, 999)}",
        "unit_type": unit_type,
        "status": "DISPATCHED",
        "origin": {
            "name": origin_landmark["name"],
            "lat": origin_landmark["lat"],
            "lon": origin_landmark["lon"]
        },
        "destination": {
            "name": dest_landmark["name"],
            "lat": dest_landmark["lat"],
            "lon": dest_landmark["lon"]
        },
        "speed_kmh": speed_kmh,
        "eta_min": eta_min,
        "priority": "HIGH",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def generate_green_corridor() -> Dict[str, Any]:
    """
    Generate a synchronized green wave corridor status report for Lucknow.

    Returns
    -------
    dict
        Active corridor configuration and signal offsets.
    """
    corridor_definitions = [
        {
            "corridor_id": "corridor_trauma_rml",
            "name": "Trauma Care Emergency Corridor (KGMU Chowk -> RML Hospital)",
            "speed_kph": 45.0,
            "intersections": [
                {"node_id": "chowk", "name": "Chowk Medical Chauraha", "phase_offset_ms": 0, "green_duration_sec": 50},
                {"node_id": "it_chauraha", "name": "IT College Chauraha", "phase_offset_ms": 304000, "green_duration_sec": 45},
                {"node_id": "nishatganj", "name": "Nishatganj Bridge", "phase_offset_ms": 456000, "green_duration_sec": 45},
                {"node_id": "chauraha_1090", "name": "1090 Women Power Line", "phase_offset_ms": 640000, "green_duration_sec": 50},
                {"node_id": "patrakarpuram", "name": "Patrakarpuram Gomti Nagar", "phase_offset_ms": 864000, "green_duration_sec": 45},
                {"node_id": "lohia_hospital", "name": "Dr. RML Hospital", "phase_offset_ms": 984000, "green_duration_sec": 60}
            ]
        },
        {
            "corridor_id": "corridor_secretariat_express",
            "name": "Vidhan Sabha Secretariat Rapid Corridor",
            "speed_kph": 50.0,
            "intersections": [
                {"node_id": "charbagh", "name": "Charbagh Railway Station", "phase_offset_ms": 0, "green_duration_sec": 45},
                {"node_id": "hussainganj", "name": "Hussainganj Chauraha", "phase_offset_ms": 129600, "green_duration_sec": 40},
                {"node_id": "vidhan_sabha", "name": "Vidhan Sabha Marg", "phase_offset_ms": 216000, "green_duration_sec": 50},
                {"node_id": "hazratganj", "name": "Hazratganj Chauraha", "phase_offset_ms": 288000, "green_duration_sec": 50},
                {"node_id": "chauraha_1090", "name": "1090 Women Power Line", "phase_offset_ms": 460800, "green_duration_sec": 45}
            ]
        }
    ]

    selected = corridor_definitions[int(np.random.randint(0, len(corridor_definitions)))]

    return {
        "telemetry_type": "green_corridor_status",
        "corridor_id": selected["corridor_id"],
        "name": selected["name"],
        "status": "GREEN_WAVE_ACTIVE",
        "speed_kph": selected["speed_kph"],
        "intersections": selected["intersections"],
        "active_vehicle": f"EMERGENCY_AMB_{np.random.randint(101, 999)}",
        "duration_remaining_sec": int(np.random.randint(60, 240)),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
