"""Capacitated Vehicle Routing Problem solver using Google OR-Tools.

Solves multi-vehicle waste collection routing with:
- Vehicle capacity constraints (5000 kg per vehicle)
- Distance matrix optimization
- Time window support
- Dynamic reallocation when bins exceed 75% fill threshold
"""

from __future__ import annotations

import math
from typing import Any

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def _extract_coordinates(node: dict[str, Any]) -> tuple[float, float]:
    """Extract latitude and longitude from a node dictionary."""
    lat = node.get("lat")
    if lat is None:
        lat = node.get("latitude")
    if lat is None:
        raise ValueError(f"Node missing latitude coordinate: {node}")

    lon = node.get("lon")
    if lon is None:
        lon = node.get("lng")
    if lon is None:
        lon = node.get("longitude")
    if lon is None:
        raise ValueError(f"Node missing longitude coordinate: {node}")

    return float(lat), float(lon)


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate the great-circle distance between two points on Earth in integer meters."""
    if lat1 == lat2 and lon1 == lon2:
        return 0

    earth_radius_m = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    sin_half_dphi = math.sin(delta_phi / 2.0)
    sin_half_dlambda = math.sin(delta_lambda / 2.0)

    a = (sin_half_dphi * sin_half_dphi) + (
        math.cos(phi1) * math.cos(phi2) * sin_half_dlambda * sin_half_dlambda
    )
    # Clip to avoid floating point precision issues outside [-1.0, 1.0] range
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))

    return int(round(earth_radius_m * c))


def create_distance_matrix(nodes: list[dict[str, Any]]) -> list[list[int]]:
    """Compute Haversine distance matrix between all pairs of nodes in integer meters.

    Args:
        nodes: List of node dictionaries containing lat/latitude and lon/lng/longitude.

    Returns:
        Square 2D list of integer distances in meters.
    """
    n = len(nodes)
    coords = [_extract_coordinates(node) for node in nodes]
    matrix: list[list[int]] = [[0] * n for _ in range(n)]

    for i in range(n):
        lat_i, lon_i = coords[i]
        for j in range(i + 1, n):
            lat_j, lon_j = coords[j]
            dist = _haversine_distance_meters(lat_i, lon_i, lat_j, lon_j)
            matrix[i][j] = dist
            matrix[j][i] = dist

    return matrix


def reallocate_urgent_bins(
    nodes: list[dict[str, Any]],
    threshold_pct: float = 75.0,
) -> list[dict[str, Any]]:
    """Filter bins exceeding fill threshold and prioritize by fill percentage descending.

    Args:
        nodes: List of bin node dictionaries.
        threshold_pct: Fill percentage threshold (default 75.0).

    Returns:
        List of urgent bin dictionaries sorted by fill percentage descending.
    """
    urgent_bins: list[dict[str, Any]] = []

    for index, node in enumerate(nodes):
        # Exclude depot nodes
        if node.get("is_depot", False) or node.get("type") == "depot":
            continue

        fill = node.get("fill_pct")
        if fill is None:
            fill = node.get("fill_percentage")
        if fill is None:
            fill = node.get("fill_rate_pct")
        if fill is None:
            fill = node.get("current_pct", 0.0)

        fill_val = float(fill)
        if fill_val >= threshold_pct:
            bin_copy = dict(node)
            bin_copy["original_index"] = index
            bin_copy["fill_pct"] = fill_val
            urgent_bins.append(bin_copy)

    urgent_bins.sort(key=lambda b: float(b.get("fill_pct", 0.0)), reverse=True)
    return urgent_bins


def solve_cvrp(
    nodes: list[dict[str, Any]],
    num_vehicles: int = 6,
    vehicle_capacity: int = 5000,
    depot_index: int = 0,
) -> dict[str, Any]:
    """Solve Capacitated Vehicle Routing Problem using Google OR-Tools.

    Args:
        nodes: List of dictionaries representing nodes (depot and collection bins).
            Each node can specify 'id', 'demand' (or 'fill_kg' / 'weight_kg'),
            coordinates ('lat', 'lon'), and optional 'time_window' (start_sec, end_sec).
        num_vehicles: Number of vehicles available.
        vehicle_capacity: Maximum capacity per vehicle in kg.
        depot_index: Index of the depot node in the nodes list.

    Returns:
        Dictionary with optimization status, vehicle routes (list of node ID lists),
        total distance in km, total demand served in kg, and individual route details.
    """
    if not nodes:
        return {
            "status": "infeasible",
            "vehicle_routes": [],
            "total_distance_km": 0.0,
            "total_demand_served_kg": 0,
            "message": "Node list is empty",
            "routes_detail": [],
        }

    num_nodes = len(nodes)
    if depot_index < 0 or depot_index >= num_nodes:
        raise ValueError(f"Depot index {depot_index} out of range [0, {num_nodes - 1}]")

    if num_nodes == 1:
        depot_id = nodes[depot_index].get("id", depot_index)
        return {
            "status": "success",
            "vehicle_routes": [[depot_id] for _ in range(num_vehicles)],
            "total_distance_km": 0.0,
            "total_demand_served_kg": 0,
            "message": "Only depot present",
            "routes_detail": [
                {
                    "vehicle_id": v,
                    "route_indices": [depot_index],
                    "route_node_ids": [depot_id],
                    "distance_meters": 0,
                    "demand_kg": 0,
                }
                for v in range(num_vehicles)
            ],
        }

    # Extract node demands
    demands: list[int] = []
    for idx, node in enumerate(nodes):
        if idx == depot_index or node.get("is_depot", False) or node.get("type") == "depot":
            demands.append(0)
        else:
            d = node.get("demand")
            if d is None:
                d = node.get("fill_kg")
            if d is None:
                d = node.get("weight_kg", 0)
            demands.append(int(round(float(d))))

    # Build distance matrix
    distance_matrix = create_distance_matrix(nodes)

    # Initialize RoutingIndexManager and RoutingModel
    manager = pywrapcp.RoutingIndexManager(num_nodes, num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    # Register distance callback
    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add capacity constraint
    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [vehicle_capacity] * num_vehicles,
        True,  # start cumul to zero
        "Capacity",
    )

    # Check for optional time windows
    has_time_windows = any("time_window" in node for node in nodes)
    if has_time_windows:
        # Time callback considers travel time (assumed 30 km/h = 8.33 m/s) + service time
        def time_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_sec = int(round(distance_matrix[from_node][to_node] / 8.333))
            service_sec = int(nodes[from_node].get("service_time_seconds", 120))
            return travel_sec + service_sec

        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            3600,  # allow waiting time up to 1 hour
            86400,  # maximum route duration (24h)
            False,  # don't force start cumul to zero
            "Time",
        )
        time_dimension = routing.GetDimensionOrDie("Time")
        for node_idx, node in enumerate(nodes):
            if "time_window" in node:
                start_w, end_w = node["time_window"]
                index = manager.NodeToIndex(node_idx)
                if index != -1:
                    time_dimension.CumulVar(index).SetRange(int(start_w), int(end_w))

    # Configure search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30

    # Solve CVRP
    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {
            "status": "infeasible",
            "vehicle_routes": [],
            "total_distance_km": 0.0,
            "total_demand_served_kg": 0,
            "message": "No feasible routing solution found within constraints",
            "routes_detail": [],
        }

    total_distance_meters = 0
    total_demand_kg = 0
    vehicle_routes: list[list[Any]] = []
    routes_detail: list[dict[str, Any]] = []

    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route_nodes: list[int] = []
        route_node_ids: list[Any] = []
        route_distance = 0
        route_demand = 0

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_nodes.append(node_index)
            node_id = nodes[node_index].get("id", node_index)
            route_node_ids.append(node_id)
            route_demand += demands[node_index]

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

        # Append end depot
        end_node_index = manager.IndexToNode(index)
        route_nodes.append(end_node_index)
        end_node_id = nodes[end_node_index].get("id", end_node_index)
        route_node_ids.append(end_node_id)

        vehicle_routes.append(route_node_ids)
        total_distance_meters += route_distance
        total_demand_kg += route_demand

        routes_detail.append(
            {
                "vehicle_id": vehicle_id,
                "route_indices": route_nodes,
                "route_node_ids": route_node_ids,
                "distance_meters": route_distance,
                "distance_km": round(route_distance / 1000.0, 3),
                "demand_kg": route_demand,
            }
        )

    return {
        "status": "success",
        "vehicle_routes": vehicle_routes,
        "total_distance_km": round(total_distance_meters / 1000.0, 3),
        "total_demand_served_kg": total_demand_kg,
        "num_vehicles_used": sum(1 for r in routes_detail if len(r["route_indices"]) > 2),
        "routes_detail": routes_detail,
    }
