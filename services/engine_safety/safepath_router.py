"""SafePath impedance routing engine for urban women and citizen safety.

Implements safety impedance routing using NetworkX with multi-factor risk
weighting (luminosity, CCTV density, patrol proximity, and Pink Booths).
"""

from __future__ import annotations

import math
import uuid
from typing import Any
import networkx as nx

# SafePath impedance weights
WEIGHT_LUMINOSITY = 0.35
WEIGHT_CCTV = 0.30
WEIGHT_PATROL = 0.20
WEIGHT_PINK_BOOTH = 0.15

# Landmark coordinates in Lucknow (lat, lon)
LUCKNOW_LANDMARKS: dict[str, tuple[float, float]] = {
    "Hazratganj": (26.8467, 80.9462),
    "Aminabad": (26.8520, 80.9220),
    "Gomti Nagar": (26.8563, 80.9800),
    "Alambagh": (26.8075, 80.9050),
    "Charbagh": (26.8580, 80.9215),
    "Indira Nagar": (26.8750, 80.9950),
    "Aliganj": (26.8870, 80.9380),
    "Mahanagar": (26.8720, 80.9330),
    "Kaiserbagh": (26.8450, 80.9380),
    "Cantonment": (26.8380, 80.9250),
    "Rajajipuram": (26.8550, 80.8950),
    "Vikas Nagar": (26.8670, 80.9130),
    "Husainabad": (26.8690, 80.9200),
    "Narhi": (26.8560, 80.9420),
    "Lalbagh": (26.8500, 80.9350),
    "Thakurganj": (26.8700, 80.9150),
    "Saadatganj": (26.8600, 80.9300),
    "Naka Hindola": (26.8650, 80.9230),
    "Daliganj": (26.8800, 80.9420),
    "IT Crossing": (26.8550, 80.9700),
    "Faizabad Road": (26.8800, 80.9600),
    "Chinhat": (26.8900, 80.9900),
    "Jankipuram": (26.9100, 80.9700),
    "Ashiyana": (26.7900, 80.9200),
    "Telibagh": (26.7800, 80.9400),
}


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two coordinates."""
    earth_radius_m = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_m * c


def safepath_impedance(edge_data: dict[str, Any]) -> float:
    """Calculate SafePath impedance (Z_s) for an edge.

    Formula:
    Z_s = Distance / (w1 * L_lum + w2 * rho_cctv + w3 * (1 / (d_patrol + 1)) + w4 * B_pink)
    """
    distance_m = float(edge_data.get("distance_m", 1000.0))
    l_lum = float(edge_data.get("luminosity", 0.5))
    rho_cctv = float(edge_data.get("cctv_density", 0.5))
    d_patrol = float(edge_data.get("patrol_distance_km", 1.0))
    b_pink = float(edge_data.get("pink_booth", 0))

    denominator = (
        WEIGHT_LUMINOSITY * l_lum
        + WEIGHT_CCTV * rho_cctv
        + WEIGHT_PATROL * (1.0 / (d_patrol + 1.0))
        + WEIGHT_PINK_BOOTH * b_pink
    )

    if denominator <= 0.0:
        denominator = 1e-6

    return distance_m / denominator


def build_safety_graph() -> nx.Graph:
    """Create a weighted NetworkX graph of Lucknow with >= 25 nodes and >= 40 edges.

    Each edge has attributes:
    - distance_m (float)
    - luminosity (0-1 float)
    - cctv_density (0-1 float)
    - patrol_distance_km (float)
    - pink_booth (0 or 1 int)
    - safepath_impedance (float)
    """
    g = nx.Graph()

    # Add landmarks as nodes
    for name, (lat, lon) in LUCKNOW_LANDMARKS.items():
        g.add_node(name, lat=lat, lon=lon)

    # Edge definitions between landmarks: (u, v, lum, cctv, patrol_km, pink_booth, road_factor)
    edge_specs: list[tuple[str, str, float, float, float, int, float]] = [
        # Central Hubs: Hazratganj / Narhi / Lalbagh / Kaiserbagh
        ("Hazratganj", "Narhi", 0.94, 0.92, 0.3, 1, 1.15),
        ("Hazratganj", "Lalbagh", 0.91, 0.88, 0.4, 1, 1.12),
        ("Hazratganj", "Kaiserbagh", 0.89, 0.85, 0.5, 1, 1.18),
        ("Hazratganj", "IT Crossing", 0.88, 0.82, 0.6, 1, 1.20),
        ("Hazratganj", "Gomti Nagar", 0.92, 0.90, 0.5, 1, 1.22),
        ("Hazratganj", "Cantonment", 0.85, 0.78, 0.8, 0, 1.15),
        ("Narhi", "IT Crossing", 0.86, 0.80, 0.5, 0, 1.16),
        ("Narhi", "Lalbagh", 0.82, 0.75, 0.7, 0, 1.14),
        ("Lalbagh", "Kaiserbagh", 0.85, 0.80, 0.5, 1, 1.15),
        ("Lalbagh", "Aminabad", 0.76, 0.72, 0.8, 0, 1.20),
        ("Lalbagh", "Charbagh", 0.84, 0.86, 0.6, 1, 1.16),

        # Old City & Charbagh Corridor
        ("Kaiserbagh", "Aminabad", 0.74, 0.68, 0.9, 0, 1.22),
        ("Kaiserbagh", "Cantonment", 0.80, 0.70, 1.0, 0, 1.18),
        ("Kaiserbagh", "Daliganj", 0.68, 0.60, 1.2, 0, 1.25),
        ("Aminabad", "Charbagh", 0.86, 0.85, 0.4, 1, 1.15),
        ("Aminabad", "Naka Hindola", 0.70, 0.65, 0.8, 0, 1.20),
        ("Charbagh", "Naka Hindola", 0.88, 0.84, 0.3, 1, 1.12),
        ("Charbagh", "Alambagh", 0.87, 0.89, 0.5, 1, 1.15),
        ("Charbagh", "Cantonment", 0.82, 0.79, 0.7, 0, 1.14),

        # South Lucknow: Alambagh, Ashiyana, Telibagh, Cantonment
        ("Alambagh", "Ashiyana", 0.83, 0.75, 0.6, 1, 1.16),
        ("Alambagh", "Rajajipuram", 0.72, 0.64, 1.1, 0, 1.25),
        ("Ashiyana", "Telibagh", 0.75, 0.68, 0.9, 1, 1.20),
        ("Cantonment", "Telibagh", 0.79, 0.71, 0.8, 0, 1.18),

        # West Lucknow: Rajajipuram, Saadatganj, Husainabad, Thakurganj
        ("Rajajipuram", "Saadatganj", 0.62, 0.52, 1.4, 0, 1.24),
        ("Saadatganj", "Husainabad", 0.65, 0.58, 1.3, 0, 1.22),
        ("Saadatganj", "Thakurganj", 0.60, 0.50, 1.5, 0, 1.26),
        ("Saadatganj", "Naka Hindola", 0.64, 0.55, 1.3, 0, 1.25),
        ("Husainabad", "Thakurganj", 0.70, 0.62, 1.1, 0, 1.18),
        ("Husainabad", "Naka Hindola", 0.66, 0.58, 1.2, 0, 1.24),
        ("Husainabad", "Daliganj", 0.69, 0.61, 1.1, 0, 1.20),

        # North-West / North: Thakurganj, Vikas Nagar, Daliganj, Aliganj, Mahanagar
        ("Thakurganj", "Vikas Nagar", 0.63, 0.54, 1.4, 0, 1.26),
        ("Vikas Nagar", "Daliganj", 0.71, 0.66, 1.0, 0, 1.20),
        ("Vikas Nagar", "Aliganj", 0.81, 0.75, 0.7, 1, 1.15),
        ("Daliganj", "Mahanagar", 0.78, 0.72, 0.8, 0, 1.18),
        ("Daliganj", "Aliganj", 0.77, 0.70, 0.9, 0, 1.16),
        ("Aliganj", "Mahanagar", 0.88, 0.85, 0.5, 1, 1.14),
        ("Aliganj", "Jankipuram", 0.80, 0.74, 0.8, 1, 1.18),

        # Trans-Gomti / East: Mahanagar, IT Crossing, Gomti Nagar, Faizabad Road, Indira Nagar, Chinhat
        ("Mahanagar", "IT Crossing", 0.87, 0.84, 0.5, 0, 1.14),
        ("Mahanagar", "Faizabad Road", 0.85, 0.80, 0.6, 0, 1.15),
        ("IT Crossing", "Faizabad Road", 0.89, 0.83, 0.5, 1, 1.14),
        ("IT Crossing", "Gomti Nagar", 0.91, 0.88, 0.4, 1, 1.16),
        ("Faizabad Road", "Indira Nagar", 0.86, 0.81, 0.6, 1, 1.15),
        ("Faizabad Road", "Chinhat", 0.75, 0.67, 1.1, 0, 1.22),
        ("Faizabad Road", "Jankipuram", 0.78, 0.70, 0.9, 0, 1.20),
        ("Gomti Nagar", "Indira Nagar", 0.90, 0.87, 0.5, 1, 1.15),
        ("Gomti Nagar", "Chinhat", 0.82, 0.78, 0.8, 1, 1.20),
        ("Indira Nagar", "Chinhat", 0.80, 0.72, 0.9, 0, 1.18),
    ]

    for u, v, lum, cctv, patrol_km, pink_booth, road_factor in edge_specs:
        lat1, lon1 = LUCKNOW_LANDMARKS[u]
        lat2, lon2 = LUCKNOW_LANDMARKS[v]
        raw_dist = haversine_distance_m(lat1, lon1, lat2, lon2)
        dist_m = round(raw_dist * road_factor, 1)

        edge_data = {
            "distance_m": dist_m,
            "luminosity": lum,
            "cctv_density": cctv,
            "patrol_distance_km": patrol_km,
            "pink_booth": pink_booth,
        }
        edge_data["safepath_impedance"] = safepath_impedance(edge_data)
        g.add_edge(u, v, **edge_data)

    return g


# Cache default graph
_GLOBAL_SAFETY_GRAPH: nx.Graph | None = None


def get_default_safety_graph() -> nx.Graph:
    """Return singleton instance of Lucknow safety graph."""
    global _GLOBAL_SAFETY_GRAPH
    if _GLOBAL_SAFETY_GRAPH is None:
        _GLOBAL_SAFETY_GRAPH = build_safety_graph()
    return _GLOBAL_SAFETY_GRAPH


def _calculate_route_metrics(
    graph: nx.Graph, path: list[str]
) -> tuple[float, float, float, list[dict[str, Any]]]:
    """Calculate distance, duration, safety score, and blind spots along a path."""
    total_distance_m = 0.0
    weighted_safety_sum = 0.0
    blind_spots: list[dict[str, Any]] = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge = graph[u][v]
        d_m = float(edge["distance_m"])
        lum = float(edge["luminosity"])
        cctv = float(edge["cctv_density"])
        patrol = float(edge["patrol_distance_km"])
        pink = float(edge["pink_booth"])

        total_distance_m += d_m

        # Segment safety index between 0.0 and 1.0
        seg_safety = (
            WEIGHT_LUMINOSITY * lum
            + WEIGHT_CCTV * cctv
            + WEIGHT_PATROL * (1.0 / (patrol + 1.0))
            + WEIGHT_PINK_BOOTH * pink
        )
        weighted_safety_sum += seg_safety * d_m

        if cctv < 0.65 or lum < 0.65:
            blind_spots.append({
                "segment": f"{u} → {v}",
                "start_node": u,
                "end_node": v,
                "luminosity": lum,
                "cctv_density": cctv,
                "reason": "Low luminosity or sparse CCTV coverage",
            })

    dist_km = total_distance_m / 1000.0
    # Average speed in city walking/transit ~ 25 km/h
    duration_min = (dist_km / 25.0) * 60.0

    if total_distance_m > 0:
        safety_score = (weighted_safety_sum / total_distance_m) * 100.0
    else:
        safety_score = 90.0

    return dist_km, duration_min, safety_score, blind_spots


def compute_safepath(
    origin: str, destination: str, graph: nx.Graph | None = None
) -> dict[str, Any]:
    """Compute both the shortest route (Route A) and the SafePath route (Route B).

    Route A: Shortest path by distance (Dijkstra weight='distance_m').
             Color: #F43F5E (crimson, dashed).
    Route B: SafePath impedance (Dijkstra weight='safepath_impedance').
             Color: #10B981 (emerald, glowing).

    Returns:
    {
        route_a: {route_id, waypoints, distance_km, duration_min, safety_score, color_hex},
        route_b: {route_id, waypoints, distance_km, duration_min, safety_score, color_hex},
        surveillance_status: str,
        blind_spots: list
    }
    """
    if graph is None:
        graph = get_default_safety_graph()

    # Case-insensitive resolution of landmark names
    node_lookup = {node.lower(): node for node in graph.nodes}
    resolved_origin = node_lookup.get(origin.lower().strip())
    resolved_dest = node_lookup.get(destination.lower().strip())

    if not resolved_origin:
        raise ValueError(f"Origin '{origin}' not found in Lucknow safety network.")
    if not resolved_dest:
        raise ValueError(f"Destination '{destination}' not found in Lucknow safety network.")

    # Route A: Shortest distance path
    path_a = nx.shortest_path(
        graph, source=resolved_origin, target=resolved_dest, weight="distance_m"
    )
    dist_a_km, dur_a_min, score_a, blind_spots_a = _calculate_route_metrics(graph, path_a)

    # Route B: SafePath impedance path
    path_b = nx.shortest_path(
        graph, source=resolved_origin, target=resolved_dest, weight="safepath_impedance"
    )
    dist_b_km, dur_b_min, score_b, blind_spots_b = _calculate_route_metrics(graph, path_b)

    # Waypoints formatting
    waypoints_a = [
        {
            "name": n,
            "lat": graph.nodes[n]["lat"],
            "lon": graph.nodes[n]["lon"],
        }
        for n in path_a
    ]

    waypoints_b = [
        {
            "name": n,
            "lat": graph.nodes[n]["lat"],
            "lon": graph.nodes[n]["lon"],
        }
        for n in path_b
    ]

    # Overall surveillance status around destination
    dest_lat = graph.nodes[resolved_dest]["lat"]
    dest_lon = graph.nodes[resolved_dest]["lon"]
    surveillance_status = get_surveillance_status(dest_lat, dest_lon, graph)

    return {
        "route_a": {
            "route_id": f"route_dist_{uuid.uuid4().hex[:8]}",
            "name": "Shortest Distance Route",
            "waypoints": waypoints_a,
            "distance_km": round(dist_a_km, 2),
            "duration_min": round(dur_a_min, 1),
            "safety_score": round(score_a, 1),
            "color_hex": "#F43F5E",
            "style": "dashed",
            "mode": "shortest_path",
        },
        "route_b": {
            "route_id": f"route_safe_{uuid.uuid4().hex[:8]}",
            "name": "SafePath AI Escort Route",
            "waypoints": waypoints_b,
            "distance_km": round(dist_b_km, 2),
            "duration_min": round(dur_b_min, 1),
            "safety_score": round(score_b, 1),
            "color_hex": "#10B981",
            "style": "glowing",
            "mode": "impedance_safepath",
        },
        "surveillance_status": surveillance_status,
        "blind_spots": blind_spots_a,
        "safepath_blind_spots": blind_spots_b,
    }


def get_surveillance_status(
    lat: float, lon: float, graph: nx.Graph | None = None
) -> str:
    """Check if coordinate is within CCTV coverage.

    Returns:
    - SURVEILLANCE_LOCKED
    - BLIND_SPOT_DETECTED
    - OUT_OF_RANGE
    """
    if graph is None:
        graph = get_default_safety_graph()

    min_dist = float("inf")
    closest_node = None

    for node, data in graph.nodes(data=True):
        d = haversine_distance_m(lat, lon, data["lat"], data["lon"])
        if d < min_dist:
            min_dist = d
            closest_node = node

    # If further than 8 km from any known Lucknow hub
    if min_dist > 8000.0 or closest_node is None:
        return "OUT_OF_RANGE"

    # Within 1.5 km of a major node, check average CCTV density of adjacent edges
    adjacent_edges = list(graph.edges(closest_node, data=True))
    if not adjacent_edges:
        return "BLIND_SPOT_DETECTED"

    avg_cctv = sum(float(edge_data.get("cctv_density", 0.0)) for _, _, edge_data in adjacent_edges) / len(adjacent_edges)
    pink_present = any(edge_data.get("pink_booth", 0) == 1 for _, _, edge_data in adjacent_edges)

    if min_dist <= 1200.0 and (avg_cctv >= 0.70 or pink_present):
        return "SURVEILLANCE_LOCKED"
    elif min_dist <= 3000.0:
        return "BLIND_SPOT_DETECTED"
    else:
        return "OUT_OF_RANGE"
