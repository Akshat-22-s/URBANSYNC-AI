"""
UrbanSync AI - Unit Tests for Mobility Engine and Telemetry Simulator
=====================================================================
"""

import unittest
from datetime import datetime, timedelta, timezone

from services.engine_mobility.siln_calculator import (
    calculate_departure,
    calculate_dynamic_buffer,
    check_reroute,
)
from services.engine_mobility.dynamic_graph import (
    DynamicGraph,
    build_sample_network,
)
from services.engine_mobility.green_wave import (
    compute_green_wave,
    optimize_corridor,
    get_active_corridors,
    haversine_distance_m,
)
from services.simulator.mock_streams import (
    generate_citizen_packet,
    generate_dispatch_event,
    generate_green_corridor,
    generate_snatch_event,
    generate_waste_update,
    get_initial_bins,
    get_initial_citizens,
)


class TestSILNCalculator(unittest.TestCase):
    def test_calculate_dynamic_buffer(self):
        buf = calculate_dynamic_buffer(parking_min=6.0, toll_min=2.5, weather_min=1.5)
        self.assertEqual(buf["parking_min"], 6.0)
        self.assertEqual(buf["toll_min"], 2.5)
        self.assertEqual(buf["weather_min"], 1.5)
        self.assertEqual(buf["total"], 10.0)

    def test_calculate_departure_urgencies(self):
        ref_time = datetime(2026, 10, 15, 9, 0, 0)

        # 1. PLENTY_OF_TIME (> 30 min lead time)
        # Event at 10:30. Arrive by 10:25. Transit: 15 min, buffer: 5 min -> Depart at 10:05.
        # Lead time from 9:00 = 65 min.
        res = calculate_departure(
            event_time=ref_time + timedelta(minutes=90),
            transit_duration_min=15.0,
            parking_min=5.0,
            current_time=ref_time
        )
        self.assertEqual(res["urgency"], "PLENTY_OF_TIME")
        self.assertGreater(res["lead_time_min"], 30.0)

        # 2. LEAVE_SOON (15 to 30 min lead time)
        # Event at 9:45. Arrive by 9:40. Transit: 15 min, buffer: 5 min -> Depart at 9:20.
        # Lead time from 9:00 = 20 min.
        res = calculate_departure(
            event_time=ref_time + timedelta(minutes=45),
            transit_duration_min=15.0,
            parking_min=5.0,
            current_time=ref_time
        )
        self.assertEqual(res["urgency"], "LEAVE_SOON")
        self.assertEqual(res["lead_time_min"], 20.0)

        # 3. LEAVE_NOW (5 to 15 min lead time)
        # Event at 9:32. Arrive by 9:27. Transit: 15 min, buffer: 5 min -> Depart at 9:07.
        # Lead time from 9:00 = 7 min.
        res = calculate_departure(
            event_time=ref_time + timedelta(minutes=32),
            transit_duration_min=15.0,
            parking_min=5.0,
            current_time=ref_time
        )
        self.assertEqual(res["urgency"], "LEAVE_NOW")
        self.assertEqual(res["lead_time_min"], 7.0)

        # 4. LATE (< 5 min lead time)
        # Event at 9:22. Arrive by 9:17. Transit: 15 min, buffer: 5 min -> Depart at 8:57.
        # Lead time from 9:00 = -3 min.
        res = calculate_departure(
            event_time=ref_time + timedelta(minutes=22),
            transit_duration_min=15.0,
            parking_min=5.0,
            current_time=ref_time
        )
        self.assertEqual(res["urgency"], "LATE")
        self.assertLess(res["lead_time_min"], 5.0)

    def test_check_reroute(self):
        # Case 1: Delay > 4 min and saved >= 3 min -> Should reroute
        res = check_reroute(current_delay_min=5.0, current_eta_min=20.0, detour_eta_min=16.0)
        self.assertTrue(res["should_reroute"])
        self.assertEqual(res["time_saved_min"], 4.0)

        # Case 2: Delay <= 4 min -> Should not reroute
        res = check_reroute(current_delay_min=3.5, current_eta_min=20.0, detour_eta_min=15.0)
        self.assertFalse(res["should_reroute"])

        # Case 3: Delay > 4 min but time saved < 3 min -> Should not reroute
        res = check_reroute(current_delay_min=6.0, current_eta_min=20.0, detour_eta_min=18.0)
        self.assertFalse(res["should_reroute"])
        self.assertEqual(res["time_saved_min"], 2.0)


class TestDynamicGraph(unittest.TestCase):
    def setUp(self):
        self.network = build_sample_network()

    def test_sample_network_size(self):
        self.assertGreaterEqual(len(self.network.graph.nodes), 20)
        self.assertGreaterEqual(len(self.network.graph.edges), 30)

    def test_shortest_path(self):
        res = self.network.shortest_path("charbagh", "hazratganj")
        self.assertIn("path", res)
        self.assertEqual(res["path"][0], "charbagh")
        self.assertEqual(res["path"][-1], "hazratganj")
        self.assertGreater(res["distance_km"], 0.0)
        self.assertGreater(res["duration_min"], 0.0)
        self.assertEqual(len(res["waypoints"]), len(res["path"]))

    def test_safest_path(self):
        res = self.network.safest_path("charbagh", "vibhuti_khand")
        self.assertIn("path", res)
        self.assertIn("safety_score", res)
        self.assertGreater(res["safety_score"], 0.0)
        self.assertLessEqual(res["safety_score"], 100.0)

    def test_update_traffic_and_find_bottlenecks(self):
        self.network.update_traffic("charbagh", "hussainganj", congestion_factor=3.0)
        bottlenecks = self.network.find_bottlenecks(threshold_factor=2.0)
        self.assertTrue(any(b["from"] == "charbagh" and b["to"] == "hussainganj" for b in bottlenecks))

    def test_get_detour(self):
        detour = self.network.get_detour(
            origin="charbagh",
            destination="hazratganj",
            avoid_edges=[("charbagh", "hussainganj")]
        )
        self.assertIn("path", detour)
        # Verify the avoided edge is not traversed
        path_edges = list(zip(detour["path"][:-1], detour["path"][1:]))
        self.assertNotIn(("charbagh", "hussainganj"), path_edges)


class TestGreenWaveOptimizer(unittest.TestCase):
    def test_compute_green_wave(self):
        intersections = [
            {"id": "int_01", "name": "Intersection 1", "distance_from_prev_m": 0.0},
            {"id": "int_02", "name": "Intersection 2", "distance_from_prev_m": 500.0},
            {"id": "int_03", "name": "Intersection 3", "distance_from_prev_m": 500.0},
        ]
        result = compute_green_wave(intersections, target_speed_kph=36.0)  # 36 km/h = 10 m/s
        self.assertEqual(result["speed_kph"], 36.0)
        self.assertEqual(len(result["phase_offset_ms"]), 3)
        self.assertEqual(result["phase_offset_ms"][0], 0)
        # 500m / 10 m/s = 50s -> 50,000 ms
        self.assertEqual(result["phase_offset_ms"][1], 50000)
        # 1000m / 10 m/s = 100s -> 100,000 ms
        self.assertEqual(result["phase_offset_ms"][2], 100000)

    def test_optimize_corridor(self):
        graph = build_sample_network()
        nodes = ["charbagh", "hussainganj", "vidhan_sabha", "hazratganj"]
        result = optimize_corridor(nodes, graph, target_speed_kph=40.0)
        self.assertEqual(len(result["intersections"]), 4)
        self.assertEqual(len(result["phase_offset_ms"]), 4)

    def test_get_active_corridors(self):
        corridors = get_active_corridors()
        self.assertGreaterEqual(len(corridors), 3)
        for c in corridors:
            self.assertIn("corridor_id", c)
            self.assertIn("corridor_nodes", c)
            self.assertIn("target_speed_kph", c)


class TestSimulatorMockStreams(unittest.TestCase):
    def test_citizens_generation(self):
        citizens = get_initial_citizens(50)
        self.assertEqual(len(citizens), 50)
        first = citizens[0]
        self.assertIn("citizen_id", first)
        self.assertIn("lat", first)
        self.assertIn("lon", first)

        pkt = generate_citizen_packet(first["citizen_id"], first["lat"], first["lon"])
        self.assertEqual(pkt["citizen_id"], first["citizen_id"])
        self.assertIn("heading", pkt)
        self.assertIn("speed_mps", pkt)
        self.assertIn("accel_g", pkt)

    def test_bins_generation(self):
        bins = get_initial_bins(30)
        self.assertEqual(len(bins), 30)
        b = bins[0]
        update = generate_waste_update(b["bin_id"], b["current_fill_pct"])
        self.assertEqual(update["bin_id"], b["bin_id"])
        self.assertIn("current_fill_pct", update)
        self.assertIn("status", update)

    def test_snatch_event_accel_threshold(self):
        snatch = generate_snatch_event("cit_999", 26.8467, 80.9462)
        self.assertEqual(snatch["event_type"], "SNATCH_DETECTED")
        self.assertGreater(snatch["accel_g"], 3.0)
        self.assertIn("jerk_g_per_sec", snatch)

    def test_dispatch_and_green_corridor_events(self):
        dispatch = generate_dispatch_event()
        self.assertEqual(dispatch["telemetry_type"], "emergency_dispatch")
        self.assertIn("unit_id", dispatch)
        self.assertIn("eta_min", dispatch)

        corridor = generate_green_corridor()
        self.assertEqual(corridor["telemetry_type"], "green_corridor_status")
        self.assertIn("intersections", corridor)


if __name__ == "__main__":
    unittest.main()
