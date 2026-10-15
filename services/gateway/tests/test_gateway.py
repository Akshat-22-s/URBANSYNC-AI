"""
UrbanSync AI - Gateway Unit & Integration Test Suite.
Validates all REST endpoints, Pydantic model serialization, error cases, and fallbacks.
"""

from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from services.gateway.main import app
from services.gateway.models import (
    Coordinate,
    DispatchEvent,
    UrgencyState,
    SurveillanceStatus,
    PinType,
    EscalationCode,
)

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "UrbanSync AI Central API Gateway"
    assert data["status"] == "OPERATIONAL"
    assert "subsystems" in data


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_ws_connections" in data


def test_dispatch_events_flow():
    # List initial seeded events
    response = client.get("/api/dispatch/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 3

    # Create new event
    new_evt = {
        "event_id": "TEST-EVT-999",
        "event_type": "SNATCH_ALERT",
        "lat": 12.9750,
        "lon": 77.5920,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"citizen_id": "TEST-CITIZEN-01", "speed": 15.2},
        "severity": "CRITICAL",
    }
    create_res = client.post("/api/dispatch/events", json=new_evt)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["event_id"] == "TEST-EVT-999"
    assert created["payload"]["auto_dispatched"] is True

    # Retrieve specific event
    get_res = client.get("/api/dispatch/events/TEST-EVT-999")
    assert get_res.status_code == 200
    assert get_res.json()["event_id"] == "TEST-EVT-999"

    # Filter events
    filter_res = client.get("/api/dispatch/events?severity=CRITICAL")
    assert filter_res.status_code == 200
    for ev in filter_res.json():
        assert ev["severity"] == "CRITICAL"


def test_mobility_trip_plan():
    target_time = datetime.now(timezone.utc) + timedelta(minutes=45)
    payload = {
        "destination": {"lat": 12.9850, "lon": 77.6100},
        "event_time": target_time.isoformat(),
        "origin": {"lat": 12.9716, "lon": 77.5946},
        "vehicle_type": "car",
    }
    response = client.post("/api/mobility/trip-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "transit_duration_min" in data
    assert "dynamic_buffer" in data
    assert data["dynamic_buffer"]["total"] > 0
    assert "urgency" in data
    assert data["urgency"] in [u.value for u in UrgencyState]


def test_mobility_reroute_check():
    # Beneficial reroute case
    payload_beneficial = {
        "current_delay_min": 15.0,
        "current_eta_min": 20.0,
        "detour_eta_min": 24.0,
        "route_id": "ROUTE-101",
    }
    res = client.post("/api/mobility/reroute-check", json=payload_beneficial)
    assert res.status_code == 200
    data = res.json()
    assert data["beneficial"] is True
    assert data["recommended_action"] == "REROUTE"
    assert data["time_saved_min"] == 11.0

    # Non-beneficial reroute case
    payload_non_beneficial = {
        "current_delay_min": 2.0,
        "current_eta_min": 15.0,
        "detour_eta_min": 18.0,
        "route_id": "ROUTE-102",
    }
    res2 = client.post("/api/mobility/reroute-check", json=payload_non_beneficial)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["beneficial"] is False
    assert data2["recommended_action"] == "STAY_ON_ROUTE"


def test_mobility_green_corridors():
    res = client.get("/api/mobility/green-corridors")
    assert res.status_code == 200
    corridors = res.json()
    assert len(corridors) >= 1
    assert "phase_offset_ms" in corridors[0]


def test_mobility_navigate():
    payload = {
        "origin": {"lat": 12.9716, "lon": 77.5946},
        "destination": {"lat": 12.9850, "lon": 77.6100},
        "mode": "driving",
    }
    res = client.post("/api/mobility/navigate", json=payload)
    assert res.status_code == 200
    route = res.json()
    assert len(route["waypoints"]) >= 2
    assert route["distance_km"] > 0
    assert route["duration_min"] > 0
    assert route["color_hex"] == "#06B6D4"


def test_sanitation_bins():
    # List bins
    res = client.get("/api/sanitation/bins")
    assert res.status_code == 200
    bins = res.json()
    assert len(bins) >= 5

    # Update bin
    update_res = client.post(
        "/api/sanitation/bins/BIN-CENTRAL-01/update",
        json={"fill_pct": 96.0},
    )
    assert update_res.status_code == 200
    updated_bin = update_res.json()
    assert updated_bin["fill_pct"] == 96.0
    assert updated_bin["demand_kg"] == 4800.0


def test_sanitation_optimize_routes():
    payload = {
        "max_vehicles": 2,
        "vehicle_capacity_kg": 6000.0,
    }
    res = client.post("/api/sanitation/optimize-routes", json=payload)
    assert res.status_code == 200
    solution = res.json()
    assert "vehicle_routes" in solution
    assert solution["total_demand_served_kg"] > 0
    assert solution["total_distance_km"] > 0


def test_sanitation_change_detection():
    payload = {
        "t0_image_ref": "s3://urbansync/aerial/t0/zone_b.jpg",
        "t1_image_ref": "s3://urbansync/aerial/t1/zone_b.jpg",
        "threshold": 0.25,
    }
    res = client.post("/api/sanitation/change-detection", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["delta_detected"] is True
    assert data["debris_area_sqm"] > 0
    assert data["confidence"] > 0.8


def test_sanitation_fleet_status():
    res = client.get("/api/sanitation/fleet-status")
    assert res.status_code == 200
    fleet = res.json()
    assert len(fleet) >= 3
    assert fleet[0]["vehicle_id"].startswith("TRUCK-SAN")


def test_safety_safepath():
    payload = {
        "origin": {"lat": 12.9716, "lon": 77.5946},
        "destination": {"lat": 12.9850, "lon": 77.6100},
    }
    res = client.post("/api/safety/safepath", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["route_a"]["color_hex"] == "#F43F5E"  # Crimson
    assert data["route_b"]["color_hex"] == "#10B981"  # Emerald
    assert data["route_b"]["safety_score"] > data["route_a"]["safety_score"]
    assert len(data["blind_spots"]) >= 1


def test_safety_escort_and_telemetry():
    citizen_id = "CITIZEN-TEST-42"

    # Start escort
    start_payload = {
        "citizen_id": citizen_id,
        "origin": {"lat": 12.9716, "lon": 77.5946},
        "destination": {"lat": 12.9850, "lon": 77.6100},
    }
    start_res = client.post("/api/safety/escort/start", json=start_payload)
    assert start_res.status_code == 201
    session = start_res.json()
    assert session["citizen_id"] == citizen_id
    assert session["escort_active"] is True

    # Nominal Heartbeat
    nominal_packet = {
        "citizen_id": citizen_id,
        "lat": 12.9720,
        "lon": 77.5950,
        "accel_g": 0.45,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "escort_active": True,
        "heading_deg": 45.0,
    }
    hb_res = client.post("/api/safety/escort/heartbeat", json=nominal_packet)
    assert hb_res.status_code == 200
    hb_data = hb_res.json()
    assert hb_data["status"] == "OK"
    assert hb_data["jerk_detected"] is False

    # Snatch detection Heartbeat (> 3.0g)
    snatch_packet = {
        "citizen_id": citizen_id,
        "lat": 12.9730,
        "lon": 77.5960,
        "accel_g": 4.8,  # > 3.0g
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "escort_active": True,
        "heading_deg": 90.0,
    }
    snatch_res = client.post("/api/safety/escort/heartbeat", json=snatch_packet)
    assert snatch_res.status_code == 200
    snatch_data = snatch_res.json()
    assert snatch_data["status"] == "ALERT_TRIGGERED"
    assert snatch_data["jerk_detected"] is True
    assert snatch_data["threshold_exceeded"] is True

    # Duress PIN verification ('9999')
    duress_payload = {"citizen_id": citizen_id, "pin": "9999"}
    duress_res = client.post("/api/safety/escort/verify-pin", json=duress_payload)
    assert duress_res.status_code == 200
    duress_data = duress_res.json()
    assert duress_data["pin_type"] == PinType.DURESS.value
    assert duress_data["escalation_triggered"] is True

    # Safe PIN verification ('1234')
    safe_payload = {"citizen_id": citizen_id, "pin": "1234"}
    safe_res = client.post("/api/safety/escort/verify-pin", json=safe_payload)
    assert safe_res.status_code == 200
    safe_data = safe_res.json()
    assert safe_data["pin_type"] == PinType.SAFE.value
    assert safe_data["action_taken"] == "ESCORT_DEACTIVATED"


def test_safety_escalate():
    payload = {
        "citizen_id": "CITIZEN-EMERGENCY-01",
        "lat": 12.9700,
        "lon": 77.5900,
        "pin_type": "DURESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code": "CODE_RED_P1",
    }
    res = client.post("/api/safety/escalate", json=payload)
    assert res.status_code == 201
    evt = res.json()
    assert evt["severity"] == "CRITICAL"
    assert evt["payload"]["code"] == "CODE_RED_P1"


def test_safety_surveillance_status():
    res = client.get("/api/safety/surveillance-status?lat=12.9716&lon=77.5946")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "active_cameras" in data
    assert data["status"] in [s.value for s in SurveillanceStatus]


def test_websockets():
    with client.websocket_connect("/ws/cockpit") as ws:
        ws.send_text("ping")
        assert ws.receive_text() == "pong"

    with client.websocket_connect("/ws/citizen") as ws:
        ws.send_text("ping")
        assert ws.receive_text() == "pong"

    with client.websocket_connect("/ws/field-worker") as ws:
        ws.send_text("ping")
        assert ws.receive_text() == "pong"


if __name__ == "__main__":
    print("Running tests...")
    test_root()
    print("[PASS] test_root")
    test_health()
    print("[PASS] test_health")
    test_dispatch_events_flow()
    print("[PASS] test_dispatch_events_flow")
    test_mobility_trip_plan()
    print("[PASS] test_mobility_trip_plan")
    test_mobility_reroute_check()
    print("[PASS] test_mobility_reroute_check")
    test_mobility_green_corridors()
    print("[PASS] test_mobility_green_corridors")
    test_mobility_navigate()
    print("[PASS] test_mobility_navigate")
    test_sanitation_bins()
    print("[PASS] test_sanitation_bins")
    test_sanitation_optimize_routes()
    print("[PASS] test_sanitation_optimize_routes")
    test_sanitation_change_detection()
    print("[PASS] test_sanitation_change_detection")
    test_sanitation_fleet_status()
    print("[PASS] test_sanitation_fleet_status")
    test_safety_safepath()
    print("[PASS] test_safety_safepath")
    test_safety_escort_and_telemetry()
    print("[PASS] test_safety_escort_and_telemetry")
    test_safety_escalate()
    print("[PASS] test_safety_escalate")
    test_safety_surveillance_status()
    print("[PASS] test_safety_surveillance_status")
    test_websockets()
    print("[PASS] test_websockets")
    print("ALL TESTS PASSED SUCCESSFULLY!")


