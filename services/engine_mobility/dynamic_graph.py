"""
UrbanSync AI - Dynamic Road Network Graph
=========================================
Implements a dynamic road network graph using NetworkX DiGraph for
intelligent routing, safety-weighted navigation, bottleneck detection,
and dynamic traffic updates in the city of Lucknow.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import networkx as nx


class DynamicGraph:
    """
    Dynamic graph model representing urban road infrastructure with
    real-time traffic congestion, luminosity, CCTV coverage, and safety features.
    """

    def __init__(self, populate_defaults: bool = True) -> None:
        """
        Initialize the DynamicGraph.

        Parameters
        ----------
        populate_defaults : bool, optional
            Whether to automatically populate the Lucknow sample network (default is True).
        """
        self.graph: nx.DiGraph = nx.DiGraph()
        if populate_defaults:
            self._load_lucknow_network()

    def add_node(self, node_id: str, lat: float, lon: float, **attrs: Any) -> None:
        """
        Register an intersection / landmark node in the road network.

        Parameters
        ----------
        node_id : str
            Unique identifier for the node.
        lat : float
            Geographic latitude coordinate.
        lon : float
            Geographic longitude coordinate.
        **attrs : Any
            Additional node attributes (e.g. name, type, landmark_category).
        """
        node_attrs = {
            "lat": float(lat),
            "lon": float(lon),
            "name": attrs.get("name", node_id),
            **attrs
        }
        self.graph.add_node(node_id, **node_attrs)

    def add_edge(
        self,
        u: str,
        v: str,
        distance_km: float,
        base_duration_min: float,
        **attrs: Any
    ) -> None:
        """
        Register a directed road segment between node u and node v.

        Parameters
        ----------
        u : str
            Origin node ID.
        v : str
            Destination node ID.
        distance_km : float
            Physical distance of the road corridor in kilometers.
        base_duration_min : float
            Free-flow travel duration in minutes.
        **attrs : Any
            Additional attributes (luminosity, cctv_density, patrol_proximity, pink_booth).
        """
        dist = max(0.01, float(distance_km))
        base_dur = max(0.01, float(base_duration_min))
        congestion_factor = float(attrs.get("congestion_factor", 1.0))
        current_dur = float(attrs.get("current_duration_min", base_dur * congestion_factor))

        edge_data = {
            "distance_km": dist,
            "base_duration_min": base_dur,
            "current_duration_min": current_dur,
            "congestion_factor": congestion_factor,
            "luminosity": float(attrs.get("luminosity", 70.0)),
            "cctv_density": float(attrs.get("cctv_density", 2.0)),
            "patrol_proximity": float(attrs.get("patrol_proximity", 1.0)),
            "pink_booth": bool(attrs.get("pink_booth", False)),
            "speed_limit_kph": float(attrs.get("speed_limit_kph", 40.0)),
            **attrs
        }
        self.graph.add_edge(u, v, **edge_data)

    def update_traffic(self, u: str, v: str, congestion_factor: float) -> None:
        """
        Update the congestion factor on edge (u, v) and recompute current duration.

        Parameters
        ----------
        u : str
            Origin node ID.
        v : str
            Destination node ID.
        congestion_factor : float
            Congestion multiplier (e.g. 1.0 = normal, 2.5 = 2.5x slower).
        """
        factor = max(0.1, float(congestion_factor))
        if self.graph.has_edge(u, v):
            base_dur = self.graph[u][v]["base_duration_min"]
            self.graph[u][v]["congestion_factor"] = round(factor, 3)
            self.graph[u][v]["current_duration_min"] = round(base_dur * factor, 3)
        else:
            raise KeyError(f"Edge ({u}, {v}) does not exist in graph.")

    def shortest_path(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Compute the fastest path using Dijkstra algorithm weighted by current_duration_min.

        Parameters
        ----------
        origin : str
            Origin node identifier.
        destination : str
            Destination node identifier.

        Returns
        -------
        dict
            {
                "path": list of node IDs,
                "distance_km": float,
                "duration_min": float,
                "waypoints": list of dicts with node metadata
            }
        """
        if origin not in self.graph:
            raise KeyError(f"Origin node '{origin}' not found in road graph.")
        if destination not in self.graph:
            raise KeyError(f"Destination node '{destination}' not found in road graph.")

        if origin == destination:
            node_data = self.graph.nodes[origin]
            return {
                "path": [origin],
                "distance_km": 0.0,
                "duration_min": 0.0,
                "waypoints": [{
                    "node_id": origin,
                    "lat": node_data.get("lat"),
                    "lon": node_data.get("lon"),
                    "name": node_data.get("name", origin)
                }]
            }

        try:
            path = nx.shortest_path(
                self.graph,
                source=origin,
                target=destination,
                weight="current_duration_min"
            )
        except nx.NetworkXNoPath as exc:
            raise nx.NetworkXNoPath(f"No path found between '{origin}' and '{destination}'.") from exc

        total_distance = 0.0
        total_duration = 0.0
        waypoints = []

        for i in range(len(path)):
            curr_node = path[i]
            nd = self.graph.nodes[curr_node]
            waypoints.append({
                "node_id": curr_node,
                "lat": nd.get("lat"),
                "lon": nd.get("lon"),
                "name": nd.get("name", curr_node)
            })
            if i < len(path) - 1:
                next_node = path[i + 1]
                edge_data = self.graph[curr_node][next_node]
                total_distance += edge_data.get("distance_km", 0.0)
                total_duration += edge_data.get("current_duration_min", 0.0)

        return {
            "path": path,
            "distance_km": round(total_distance, 2),
            "duration_min": round(total_duration, 2),
            "waypoints": waypoints
        }

    def safest_path(
        self,
        origin: str,
        destination: str,
        safety_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Compute the safest path evaluating luminosity, CCTV density, patrol proximity,
        and pink booth presence along each road corridor.

        Parameters
        ----------
        origin : str
            Origin node identifier.
        destination : str
            Destination node identifier.
        safety_weights : dict, optional
            Weights for components:
            - luminosity (default 0.35)
            - cctv_density (default 0.25)
            - patrol_proximity (default 0.20)
            - pink_booth (default 0.20)

        Returns
        -------
        dict
            {
                "path": list of node IDs,
                "distance_km": float,
                "duration_min": float,
                "safety_score": float (0-100),
                "waypoints": list of dicts
            }
        """
        if origin not in self.graph:
            raise KeyError(f"Origin node '{origin}' not found in road graph.")
        if destination not in self.graph:
            raise KeyError(f"Destination node '{destination}' not found in road graph.")

        weights = {
            "luminosity": 0.35,
            "cctv_density": 0.25,
            "patrol_proximity": 0.20,
            "pink_booth": 0.20
        }
        if safety_weights:
            weights.update(safety_weights)

        # Normalize weights to sum to 1.0
        w_sum = sum(weights.values()) or 1.0
        w_lum = weights["luminosity"] / w_sum
        w_cctv = weights["cctv_density"] / w_sum
        w_patrol = weights["patrol_proximity"] / w_sum
        w_pink = weights["pink_booth"] / w_sum

        def calculate_edge_safety(edge_data: Dict[str, Any]) -> float:
            # Luminosity component (0 - 100 lux scale)
            lum = min(100.0, max(0.0, float(edge_data.get("luminosity", 50.0))))

            # CCTV density: 5+ cameras/km is considered high coverage (100)
            cctv_count = float(edge_data.get("cctv_density", 2.0))
            cctv_score = min(100.0, max(0.0, cctv_count * 20.0))

            # Patrol proximity: distance in km to nearest unit; < 0.5 km = 100, > 3.0 km = 0
            patrol_dist_km = float(edge_data.get("patrol_proximity", 1.0))
            patrol_score = max(0.0, min(100.0, 100.0 - (patrol_dist_km * 33.3)))

            # Pink booth: presence gives maximum score of 100, absence gives neutral 30
            has_booth = bool(edge_data.get("pink_booth", False))
            pink_score = 100.0 if has_booth else 30.0

            composite = (
                (w_lum * lum) +
                (w_cctv * cctv_score) +
                (w_patrol * patrol_score) +
                (w_pink * pink_score)
            )
            return round(composite, 2)

        def custom_safety_cost(u: str, v: str, edge_dict: Dict[str, Any]) -> float:
            # We penalize edges that have low safety scores.
            # Higher safety -> cost multiplier closer to 1.0
            # Lower safety -> cost multiplier up to 4.5
            s_score = calculate_edge_safety(edge_dict)
            safety_penalty = 1.0 + ((100.0 - s_score) / 28.0)
            return edge_dict.get("current_duration_min", 1.0) * safety_penalty

        try:
            path = nx.shortest_path(
                self.graph,
                source=origin,
                target=destination,
                weight=custom_safety_cost
            )
        except nx.NetworkXNoPath as exc:
            raise nx.NetworkXNoPath(f"No safe path found between '{origin}' and '{destination}'.") from exc

        total_distance = 0.0
        total_duration = 0.0
        safety_scores: List[float] = []
        waypoints = []

        for i in range(len(path)):
            curr_node = path[i]
            nd = self.graph.nodes[curr_node]
            waypoints.append({
                "node_id": curr_node,
                "lat": nd.get("lat"),
                "lon": nd.get("lon"),
                "name": nd.get("name", curr_node)
            })
            if i < len(path) - 1:
                next_node = path[i + 1]
                edge_data = self.graph[curr_node][next_node]
                total_distance += edge_data.get("distance_km", 0.0)
                total_duration += edge_data.get("current_duration_min", 0.0)
                safety_scores.append(calculate_edge_safety(edge_data))

        avg_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 100.0

        return {
            "path": path,
            "distance_km": round(total_distance, 2),
            "duration_min": round(total_duration, 2),
            "safety_score": round(avg_safety, 2),
            "waypoints": waypoints
        }

    def find_bottlenecks(self, threshold_factor: float = 2.0) -> List[Dict[str, Any]]:
        """
        Identify road corridors where current travel duration exceeds
        threshold_factor times the base duration.

        Parameters
        ----------
        threshold_factor : float, optional
            Ratio multiplier threshold for bottleneck classification (default is 2.0).

        Returns
        -------
        list of dict
            List of detected bottleneck corridors with duration metrics.
        """
        bottlenecks: List[Dict[str, Any]] = []

        for u, v, data in self.graph.edges(data=True):
            base_dur = data.get("base_duration_min", 1.0)
            curr_dur = data.get("current_duration_min", base_dur)
            congestion = data.get("congestion_factor", curr_dur / base_dur if base_dur > 0 else 1.0)

            if curr_dur > (threshold_factor * base_dur):
                bottlenecks.append({
                    "from": u,
                    "to": v,
                    "base_duration_min": round(base_dur, 2),
                    "current_duration_min": round(curr_dur, 2),
                    "congestion_factor": round(congestion, 2),
                    "distance_km": round(data.get("distance_km", 0.0), 2)
                })

        bottlenecks.sort(key=lambda item: item["congestion_factor"], reverse=True)
        return bottlenecks

    def get_detour(
        self,
        origin: str,
        destination: str,
        avoid_edges: Sequence[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """
        Find an optimal alternative path strictly avoiding or heavily penalizing specified edges.

        Parameters
        ----------
        origin : str
            Origin node identifier.
        destination : str
            Destination node identifier.
        avoid_edges : sequence of (u, v) tuples
            Road corridors to avoid.

        Returns
        -------
        dict
            Detour path route metadata and avoided corridors list.
        """
        if origin not in self.graph:
            raise KeyError(f"Origin node '{origin}' not found in road graph.")
        if destination not in self.graph:
            raise KeyError(f"Destination node '{destination}' not found in road graph.")

        # Build set of normalized edges to avoid
        avoid_set = set(avoid_edges)
        for u, v in list(avoid_set):
            avoid_set.add((v, u))

        # First attempt: strictly remove the avoided edges from temporary subgraph
        subgraph = self.graph.copy()
        for u, v in avoid_set:
            if subgraph.has_edge(u, v):
                subgraph.remove_edge(u, v)

        if nx.has_path(subgraph, origin, destination):
            chosen_graph = subgraph
        else:
            # Fallback: if graph becomes disconnected, use heavy penalty on avoided edges
            chosen_graph = self.graph.copy()
            for u, v in avoid_set:
                if chosen_graph.has_edge(u, v):
                    chosen_graph[u][v]["current_duration_min"] = (
                        chosen_graph[u][v]["current_duration_min"] * 1000.0 + 500.0
                    )

        path = nx.shortest_path(
            chosen_graph,
            source=origin,
            target=destination,
            weight="current_duration_min"
        )

        total_distance = 0.0
        total_duration = 0.0
        waypoints = []

        for i in range(len(path)):
            curr_node = path[i]
            nd = self.graph.nodes[curr_node]
            waypoints.append({
                "node_id": curr_node,
                "lat": nd.get("lat"),
                "lon": nd.get("lon"),
                "name": nd.get("name", curr_node)
            })
            if i < len(path) - 1:
                next_node = path[i + 1]
                edge_data = self.graph[curr_node][next_node]
                total_distance += edge_data.get("distance_km", 0.0)
                total_duration += edge_data.get("current_duration_min", 0.0)

        return {
            "path": path,
            "distance_km": round(total_distance, 2),
            "duration_min": round(total_duration, 2),
            "waypoints": waypoints,
            "avoided_edges": list(avoid_edges)
        }

    def _load_lucknow_network(self) -> None:
        """
        Populate the graph with realistic Lucknow intersections and arterial corridors.
        Contains 24 major nodes and 72+ directed edges.
        """
        # Node Definitions: (node_id, lat, lon, name, pink_booth_nearby, cctv_count)
        nodes_data = [
            ("hazratganj", 26.8467, 80.9462, "Hazratganj Chauraha", True, 8),
            ("vidhan_sabha", 26.8428, 80.9405, "Vidhan Sabha Marg", True, 12),
            ("charbagh", 26.8322, 80.9197, "Charbagh Railway Station", True, 10),
            ("hussainganj", 26.8385, 80.9355, "Hussainganj Chauraha", False, 4),
            ("kaiserbagh", 26.8550, 80.9330, "Kaiserbagh Bus Terminal", False, 6),
            ("aminabad", 26.8450, 80.9250, "Aminabad Market", True, 5),
            ("chowk", 26.8665, 80.9042, "Chowk Old Lucknow / KGMU", False, 4),
            ("kd_singh_stadium", 26.8530, 80.9400, "KD Singh Babu Stadium", False, 6),
            ("lucknow_university", 26.8620, 80.9380, "Lucknow University", False, 5),
            ("it_chauraha", 26.8690, 80.9410, "IT College Chauraha", True, 6),
            ("mahanagar", 26.8742, 80.9472, "Mahanagar Gole Market", False, 5),
            ("nishatganj", 26.8655, 80.9570, "Nishatganj Bridge", False, 4),
            ("chauraha_1090", 26.8480, 80.9670, "1090 Women Power Line Chauraha", True, 14),
            ("patrakarpuram", 26.8563, 80.9800, "Patrakarpuram Gomti Nagar", True, 7),
            ("polytechnic", 26.8711, 80.9984, "Polytechnic Chauraha", False, 8),
            ("indira_nagar", 26.8785, 80.9902, "Indira Nagar Chauraha", False, 5),
            ("munshi_pulia", 26.8870, 80.9995, "Munshi Pulia Chauraha", False, 6),
            ("aliganj", 26.8833, 80.9392, "Aliganj Purania Chauraha", False, 4),
            ("vibhuti_khand", 26.8640, 81.0020, "Vibhuti Khand IT Park", True, 8),
            ("lohia_hospital", 26.8610, 80.9890, "Dr. RML Hospital Gomti Nagar", True, 9),
            ("alambagh", 26.8166, 80.9022, "Alambagh Bus Terminal", True, 7),
            ("transport_nagar", 26.7820, 80.8850, "Transport Nagar RTO", False, 4),
            ("telibagh", 26.7910, 80.9440, "Telibagh Chauraha", False, 3),
            ("shahid_path", 26.8105, 81.0050, "Shahid Path Gomti Nagar Extn", False, 6),
        ]

        for nid, lat, lon, name, pink, cctvs in nodes_data:
            self.add_node(
                node_id=nid,
                lat=lat,
                lon=lon,
                name=name,
                pink_booth_nearby=pink,
                cctv_count=cctvs
            )

        # Arterial Road Corridors (u, v, dist_km, base_dur_min, luminosity, cctv_per_km, patrol_km, pink_booth)
        corridors = [
            # Hazratganj Hub
            ("charbagh", "hussainganj", 1.8, 4.5, 80.0, 4.0, 0.5, True),
            ("hussainganj", "vidhan_sabha", 1.2, 3.0, 92.0, 6.0, 0.3, True),
            ("vidhan_sabha", "hazratganj", 1.0, 2.5, 95.0, 8.0, 0.2, True),
            ("hazratganj", "kd_singh_stadium", 1.1, 2.8, 88.0, 5.0, 0.4, False),
            ("kd_singh_stadium", "kaiserbagh", 1.3, 3.2, 75.0, 4.0, 0.6, False),
            ("kaiserbagh", "aminabad", 1.4, 4.0, 70.0, 3.5, 0.8, True),
            ("aminabad", "charbagh", 2.0, 5.5, 65.0, 3.0, 0.9, False),

            # West / Old Lucknow
            ("kaiserbagh", "chowk", 3.2, 8.5, 60.0, 2.5, 1.2, False),
            ("chowk", "it_chauraha", 3.8, 9.0, 62.0, 2.8, 1.0, False),
            ("kd_singh_stadium", "lucknow_university", 1.5, 3.8, 78.0, 4.0, 0.5, False),
            ("lucknow_university", "it_chauraha", 1.0, 2.2, 82.0, 5.0, 0.4, True),

            # North Lucknow (Mahanagar, Aliganj)
            ("it_chauraha", "mahanagar", 1.8, 4.2, 76.0, 3.5, 0.7, False),
            ("mahanagar", "aliganj", 2.2, 5.0, 72.0, 3.0, 0.8, False),
            ("aliganj", "munshi_pulia", 3.5, 7.5, 68.0, 2.8, 1.1, False),

            # Central River Crossings & Gomti Links
            ("it_chauraha", "nishatganj", 1.9, 4.5, 75.0, 3.8, 0.6, False),
            ("hazratganj", "nishatganj", 2.5, 5.5, 80.0, 4.2, 0.5, False),
            ("hazratganj", "chauraha_1090", 2.4, 4.8, 95.0, 7.0, 0.3, True),
            ("nishatganj", "chauraha_1090", 2.3, 4.9, 82.0, 4.5, 0.5, True),

            # East Lucknow / Gomti Nagar Hub
            ("chauraha_1090", "patrakarpuram", 2.8, 5.8, 88.0, 5.0, 0.4, True),
            ("patrakarpuram", "lohia_hospital", 1.5, 3.2, 90.0, 6.0, 0.3, True),
            ("lohia_hospital", "vibhuti_khand", 1.8, 3.8, 85.0, 5.5, 0.4, True),
            ("vibhuti_khand", "polytechnic", 2.1, 4.2, 80.0, 4.0, 0.6, False),
            ("nishatganj", "indira_nagar", 3.2, 6.8, 74.0, 3.2, 0.8, False),
            ("indira_nagar", "polytechnic", 1.6, 3.4, 78.0, 4.0, 0.5, False),
            ("indira_nagar", "munshi_pulia", 1.4, 3.0, 72.0, 3.5, 0.7, False),

            # South Corridors / Outer Ring
            ("charbagh", "alambagh", 3.0, 6.5, 75.0, 3.8, 0.7, True),
            ("alambagh", "transport_nagar", 4.5, 8.5, 68.0, 2.5, 1.0, False),
            ("charbagh", "telibagh", 6.0, 11.5, 64.0, 2.0, 1.3, False),
            ("telibagh", "shahid_path", 5.5, 8.5, 78.0, 3.5, 0.8, False),
            ("shahid_path", "patrakarpuram", 7.0, 10.5, 85.0, 4.5, 0.5, False),
            ("shahid_path", "vibhuti_khand", 6.5, 9.5, 88.0, 5.0, 0.4, True),
        ]

        # Populate bidirectional edges
        for u, v, dist, dur, lum, cctv, patrol, pink in corridors:
            self.add_edge(
                u=u,
                v=v,
                distance_km=dist,
                base_duration_min=dur,
                luminosity=lum,
                cctv_density=cctv,
                patrol_proximity=patrol,
                pink_booth=pink
            )
            # Reverse edge
            self.add_edge(
                u=v,
                v=u,
                distance_km=dist,
                base_duration_min=dur,
                luminosity=lum,
                cctv_density=cctv,
                patrol_proximity=patrol,
                pink_booth=pink
            )


def build_sample_network() -> DynamicGraph:
    """
    Factory function to construct and return a fully initialized DynamicGraph
    configured with the Lucknow road network.

    Returns
    -------
    DynamicGraph
        Instance containing 24 nodes and 60+ road edges.
    """
    return DynamicGraph(populate_defaults=True)
