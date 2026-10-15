"""
UrbanSync AI - Green Wave Corridor Optimizer
=============================================
Calculates signal progression offsets and phase coordination so emergency
vehicles or transit platoons moving at target speeds encounter green lights
at sequential signalized intersections without stopping.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance between two geographic coordinates in meters.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of first point in degrees.
    lat2, lon2 : float
        Latitude and longitude of second point in degrees.

    Returns
    -------
    float
        Distance in meters.
    """
    radius = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2 +
        math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius * c


def compute_green_wave(
    intersections: List[Dict[str, Any]],
    target_speed_kph: float = 40.0,
    corridor_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate signal phase offsets for a series of sequential intersections
    to guarantee green-wave progression at target_speed_kph.

    Parameters
    ----------
    intersections : list of dict
        Sequential list of intersection metadata dictionaries.
        Each entry may contain:
        - 'node_id' or 'id': str
        - 'name': str (optional)
        - 'distance_from_prev_m': float (or 'distance_km', 'distance_m', or lat/lon)
        - 'cycle_sec': int (optional, default 90)
        - 'green_sec': int (optional, default 45)
    target_speed_kph : float, optional
        Target design progression speed in km/h (default is 40.0).
    corridor_id : str, optional
        Unique corridor identifier (generated if omitted).

    Returns
    -------
    dict
        {
            "corridor_id": str,
            "intersections": list of enriched dicts,
            "speed_kph": float,
            "phase_offset_ms": list of int offsets in milliseconds
        }
    """
    if not intersections:
        return {
            "corridor_id": corridor_id or "gw_corridor_empty",
            "intersections": [],
            "speed_kph": float(target_speed_kph),
            "phase_offset_ms": []
        }

    speed_kph = max(5.0, float(target_speed_kph))
    # Convert speed from km/h to m/s: 1 km/h = 1000 / 3600 m/s
    speed_mps = speed_kph / 3.6

    actual_corridor_id = corridor_id or f"corridor_{intersections[0].get('node_id', intersections[0].get('id', 'origin'))}"

    enriched_intersections: List[Dict[str, Any]] = []
    cumulative_distance_m = 0.0

    prev_lat: Optional[float] = None
    prev_lon: Optional[float] = None

    for i, node in enumerate(intersections):
        nid = str(node.get("node_id") or node.get("id") or f"node_{i}")
        name = node.get("name", nid)
        cycle_sec = int(node.get("cycle_sec", 90))
        green_sec = int(node.get("green_sec", 45))

        lat = node.get("lat")
        lon = node.get("lon")

        # Determine segment distance from previous intersection
        if i == 0:
            step_distance_m = 0.0
        else:
            if "distance_from_prev_m" in node:
                step_distance_m = float(node["distance_from_prev_m"])
            elif "distance_m" in node:
                step_distance_m = float(node["distance_m"])
            elif "distance_km" in node:
                step_distance_m = float(node["distance_km"]) * 1000.0
            elif "distance_from_prev_km" in node:
                step_distance_m = float(node["distance_from_prev_km"]) * 1000.0
            elif (
                lat is not None and lon is not None and
                prev_lat is not None and prev_lon is not None
            ):
                step_distance_m = haversine_distance_m(prev_lat, prev_lon, float(lat), float(lon))
            else:
                # Default baseline 500 meters if no spatial data provided
                step_distance_m = 500.0

        cumulative_distance_m += step_distance_m
        travel_time_sec = cumulative_distance_m / speed_mps
        offset_ms = int(round(travel_time_sec * 1000.0))

        enriched = {
            "node_id": nid,
            "name": name,
            "distance_from_start_m": round(cumulative_distance_m, 1),
            "step_distance_m": round(step_distance_m, 1),
            "travel_time_sec": round(travel_time_sec, 2),
            "phase_offset_ms": offset_ms,
            "phase_offset_sec": round(travel_time_sec, 2),
            "green_duration_sec": green_sec,
            "cycle_duration_sec": cycle_sec,
            "lat": lat,
            "lon": lon
        }
        enriched_intersections.append(enriched)

        if lat is not None:
            prev_lat = float(lat)
        if lon is not None:
            prev_lon = float(lon)

    phase_offsets_list = [item["phase_offset_ms"] for item in enriched_intersections]

    return {
        "corridor_id": actual_corridor_id,
        "intersections": enriched_intersections,
        "speed_kph": speed_kph,
        "phase_offset_ms": phase_offsets_list
    }


def optimize_corridor(
    corridor_nodes: Sequence[str],
    graph: Any,
    target_speed_kph: float = 40.0
) -> Dict[str, Any]:
    """
    Extract edge distances and topology from graph, compute green wave signal timing.

    Parameters
    ----------
    corridor_nodes : sequence of str
        Ordered sequence of node IDs defining the arterial corridor.
    graph : DynamicGraph or NetworkX graph
        The road network graph instance.
    target_speed_kph : float, optional
        Design transit speed in km/h (default is 40.0).

    Returns
    -------
    dict
        Optimized green wave corridor schedule and timing offsets.
    """
    if not corridor_nodes:
        return compute_green_wave([], target_speed_kph=target_speed_kph)

    # Support DynamicGraph wrapper or raw nx.Graph
    nx_graph = graph.graph if hasattr(graph, "graph") else graph

    intersections: List[Dict[str, Any]] = []

    for i, node_id in enumerate(corridor_nodes):
        node_attrs = nx_graph.nodes.get(node_id, {})
        lat = node_attrs.get("lat")
        lon = node_attrs.get("lon")
        name = node_attrs.get("name", node_id)

        step_dist_m = 0.0
        if i > 0:
            prev_node = corridor_nodes[i - 1]
            if nx_graph.has_edge(prev_node, node_id):
                edge_data = nx_graph[prev_node][node_id]
                step_dist_km = edge_data.get("distance_km", 0.5)
                step_dist_m = step_dist_km * 1000.0
            elif (
                lat is not None and lon is not None and
                "lat" in nx_graph.nodes[prev_node] and "lon" in nx_graph.nodes[prev_node]
            ):
                p_lat = nx_graph.nodes[prev_node]["lat"]
                p_lon = nx_graph.nodes[prev_node]["lon"]
                step_dist_m = haversine_distance_m(p_lat, p_lon, lat, lon)
            else:
                step_dist_m = 600.0

        intersections.append({
            "node_id": node_id,
            "name": name,
            "distance_from_prev_m": step_dist_m,
            "lat": lat,
            "lon": lon
        })

    corridor_id = f"corridor_{corridor_nodes[0]}_to_{corridor_nodes[-1]}"
    return compute_green_wave(
        intersections=intersections,
        target_speed_kph=target_speed_kph,
        corridor_id=corridor_id
    )


def get_active_corridors() -> List[Dict[str, Any]]:
    """
    Retrieve predefined emergency corridors configured for Lucknow.

    Returns
    -------
    list of dict
        List containing at least 3 Lucknow emergency corridors with
        corridor ID, name, sequence of node IDs, target speed, and active status.
    """
    return [
        {
            "corridor_id": "corridor_trauma_rml",
            "name": "Trauma Care Emergency Corridor (KGMU Chowk -> RML Hospital)",
            "corridor_type": "EMERGENCY_MEDICAL",
            "priority": "CRITICAL",
            "status": "ACTIVE",
            "target_speed_kph": 45.0,
            "corridor_nodes": [
                "chowk",
                "it_chauraha",
                "nishatganj",
                "chauraha_1090",
                "patrakarpuram",
                "lohia_hospital"
            ],
            "description": "Rapid ambulance transit linking King George's Medical University to Dr. Ram Manohar Lohia Hospital."
        },
        {
            "corridor_id": "corridor_secretariat_express",
            "name": "Vidhan Sabha Secretariat Rapid Corridor",
            "corridor_type": "GOVERNMENT_VVIP",
            "priority": "HIGH",
            "status": "ACTIVE",
            "target_speed_kph": 50.0,
            "corridor_nodes": [
                "charbagh",
                "hussainganj",
                "vidhan_sabha",
                "hazratganj",
                "chauraha_1090"
            ],
            "description": "High-priority green wave from Charbagh Station through Vidhan Sabha to Gomti river crossing."
        },
        {
            "corridor_id": "corridor_sgpgi_lifeline",
            "name": "South Lucknow SGPGI Medical Express",
            "corridor_type": "EMERGENCY_MEDICAL",
            "priority": "CRITICAL",
            "status": "ACTIVE",
            "target_speed_kph": 50.0,
            "corridor_nodes": [
                "hazratganj",
                "vidhan_sabha",
                "charbagh",
                "telibagh",
                "shahid_path"
            ],
            "description": "Express medical route serving South Lucknow and connecting central hubs to Sanjay Gandhi PGI."
        },
        {
            "corridor_id": "corridor_gomti_tech",
            "name": "Gomti Nagar IT & Arterial Sync Wave",
            "corridor_type": "TRANSIT_ARTERIAL",
            "priority": "MEDIUM",
            "status": "STANDBY",
            "target_speed_kph": 40.0,
            "corridor_nodes": [
                "chauraha_1090",
                "patrakarpuram",
                "lohia_hospital",
                "vibhuti_khand",
                "polytechnic"
            ],
            "description": "High-throughput corridor synchronization across East Gomti Nagar commercial hubs."
        }
    ]
