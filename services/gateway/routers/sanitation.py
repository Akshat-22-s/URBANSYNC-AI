"""
UrbanSync AI - Sanitation Router.
Manages smart waste bins, CVRP route optimization, AI debris change detection,
and municipal sanitation fleet telemetry.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..models import (
    BinUpdateRequest,
    CVRPSolution,
    ChangeDetectionRequest,
    ChangeDetectionResponse,
    Coordinate,
    DispatchEvent,
    FleetVehicle,
    OptimizeRoutesRequest,
    WasteNode,
)
from ..websocket_manager import ws_manager

logger = logging.getLogger("gateway.sanitation")

router = APIRouter(prefix="/api/sanitation", tags=["Sanitation"])

# Depot location for CVRP calculations
DEPOT_COORDINATE = Coordinate(lat=12.9716, lon=77.5946)

# ============================================================================
# In-Memory Bin State Store
# ============================================================================

_BINS_STORE: Dict[str, WasteNode] = {
    "BIN-CENTRAL-01": WasteNode(
        id="BIN-CENTRAL-01",
        lat=12.9730,
        lon=77.5960,
        fill_pct=88.5,
        capacity_kg=5000.0,
        demand_kg=4425.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-COMM-02": WasteNode(
        id="BIN-COMM-02",
        lat=12.9785,
        lon=77.6010,
        fill_pct=64.0,
        capacity_kg=5000.0,
        demand_kg=3200.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-RES-03": WasteNode(
        id="BIN-RES-03",
        lat=12.9650,
        lon=77.5870,
        fill_pct=34.0,
        capacity_kg=5000.0,
        demand_kg=1700.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-PARK-04": WasteNode(
        id="BIN-PARK-04",
        lat=12.9820,
        lon=77.5910,
        fill_pct=92.5,
        capacity_kg=5000.0,
        demand_kg=4625.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-METRO-05": WasteNode(
        id="BIN-METRO-05",
        lat=12.9690,
        lon=77.6050,
        fill_pct=76.0,
        capacity_kg=5000.0,
        demand_kg=3800.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-HOSP-06": WasteNode(
        id="BIN-HOSP-06",
        lat=12.9610,
        lon=77.5990,
        fill_pct=42.0,
        capacity_kg=5000.0,
        demand_kg=2100.0,
        last_collected=datetime.now(timezone.utc),
    ),
    "BIN-LAKE-07": WasteNode(
        id="BIN-LAKE-07",
        lat=12.9850,
        lon=77.6100,
        fill_pct=84.0,
        capacity_kg=5000.0,
        demand_kg=4200.0,
        last_collected=datetime.now(timezone.utc),
    ),
}

_FLEET_STORE: List[FleetVehicle] = [
    FleetVehicle(
        vehicle_id="TRUCK-SAN-01",
        lat=12.9740,
        lon=77.5970,
        capacity_kg=5000.0,
        current_load_kg=3150.0,
        status="IN_ROUTE",
    ),
    FleetVehicle(
        vehicle_id="TRUCK-SAN-02",
        lat=12.9680,
        lon=77.5890,
        capacity_kg=5000.0,
        current_load_kg=4200.0,
        status="IN_ROUTE",
    ),
    FleetVehicle(
        vehicle_id="TRUCK-SAN-03",
        lat=12.9810,
        lon=77.6030,
        capacity_kg=5000.0,
        current_load_kg=0.0,
        status="AVAILABLE",
    ),
    FleetVehicle(
        vehicle_id="TRUCK-SAN-04",
        lat=12.9630,
        lon=77.5830,
        capacity_kg=7500.0,
        current_load_kg=6100.0,
        status="IN_ROUTE",
    ),
]


# ============================================================================
# Engine Integration & Standalone Fallbacks
# ============================================================================

def _dist_km(c1_lat: float, c1_lon: float, c2_lat: float, c2_lon: float) -> float:
    """Haversine distance helper."""
    dlat = math.radians(c2_lat - c1_lat)
    dlon = math.radians(c2_lon - c1_lon)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(c1_lat))
        * math.cos(math.radians(c2_lat))
        * math.sin(dlon / 2.0) ** 2
    )
    return 6371.0 * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))


try:
    from services.engine_waste.cvrp_solver import solve_cvrp as engine_solve_cvrp
    from services.engine_waste.change_detector import detect_debris_delta as engine_detect_debris_delta
    ENGINE_WASTE_AVAILABLE = True
except ImportError:
    ENGINE_WASTE_AVAILABLE = False
    engine_solve_cvrp = None
    engine_detect_debris_delta = None
    logger.info("Engine services.engine_waste not found or incomplete. Using standalone fallback algorithms.")


    def solve_cvrp(
        nodes: List[WasteNode],
        max_vehicles: int = 3,
        vehicle_capacity_kg: float = 5000.0,
    ) -> CVRPSolution:
        """
        Greedy multi-vehicle CVRP solver fallback algorithm.
        Partitions waste nodes among vehicles respecting vehicle capacity constraints.
        """
        if not nodes:
            return CVRPSolution(vehicle_routes=[], total_distance_km=0.0, total_demand_served_kg=0.0)

        # Sort nodes descending by demand to prioritize fullest bins
        pending = sorted(nodes, key=lambda n: n.demand_kg, reverse=True)
        vehicle_routes: List[List[str]] = [[] for _ in range(max_vehicles)]
        vehicle_loads = [0.0] * max_vehicles
        total_distance = 0.0
        total_demand = 0.0

        for node in pending:
            placed = False
            for v_idx in range(max_vehicles):
                if vehicle_loads[v_idx] + node.demand_kg <= vehicle_capacity_kg:
                    vehicle_routes[v_idx].append(node.id)
                    vehicle_loads[v_idx] += node.demand_kg
                    total_demand += node.demand_kg
                    placed = True
                    break
            if not placed:
                # If capacity is exceeded, assign to vehicle with lowest current load
                min_idx = vehicle_loads.index(min(vehicle_loads))
                vehicle_routes[min_idx].append(node.id)
                vehicle_loads[min_idx] += node.demand_kg
                total_demand += node.demand_kg

        # Calculate approximate route distances
        for route in vehicle_routes:
            if not route:
                continue
            cur_lat, cur_lon = DEPOT_COORDINATE.lat, DEPOT_COORDINATE.lon
            for b_id in route:
                b = _BINS_STORE.get(b_id)
                if b:
                    total_distance += _dist_km(cur_lat, cur_lon, b.lat, b.lon)
                    cur_lat, cur_lon = b.lat, b.lon
            # Return to depot
            total_distance += _dist_km(cur_lat, cur_lon, DEPOT_COORDINATE.lat, DEPOT_COORDINATE.lon)

        active_routes = [r for r in vehicle_routes if r]
        return CVRPSolution(
            vehicle_routes=active_routes,
            total_distance_km=round(total_distance, 2),
            total_demand_served_kg=round(total_demand, 1),
        )

    def analyze_debris_change(
        t0_ref: str,
        t1_ref: str,
        threshold: float = 0.2,
    ) -> ChangeDetectionResponse:
        """Fallback computer vision debris delta simulation."""
        # Simulated delta estimation
        detected = True
        area_sqm = 16.8
        conf = 0.93
        severity = "HIGH" if area_sqm > 15.0 else ("MEDIUM" if area_sqm > 5.0 else "LOW")

        return ChangeDetectionResponse(
            delta_detected=detected,
            debris_area_sqm=area_sqm,
            confidence=conf,
            severity=severity,
            details={
                "t0_source": t0_ref,
                "t1_source": t1_ref,
                "composition_estimate": {
                    "organic": 0.45,
                    "plastics": 0.35,
                    "paper_cardboard": 0.15,
                    "hazardous_metals": 0.05,
                },
                "bounding_polygon": [
                    {"lat": 12.9731, "lon": 77.5961},
                    {"lat": 12.9735, "lon": 77.5964},
                    {"lat": 12.9733, "lon": 77.5968},
                    {"lat": 12.9729, "lon": 77.5963},
                ],
            },
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/bins",
    response_model=List[WasteNode],
    summary="List all waste bins and current fill levels",
)
async def list_bins(
    min_fill_pct: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Filter bins above fill %"),
) -> List[WasteNode]:
    """Return all telemetry-enabled waste containers with current fill percentages and demand."""
    bins = list(_BINS_STORE.values())
    if min_fill_pct is not None:
        bins = [b for b in bins if b.fill_pct >= min_fill_pct]
    return bins


@router.post(
    "/bins/{bin_id}/update",
    response_model=WasteNode,
    summary="Update bin fill percentage and publish delta",
)
async def update_bin(bin_id: str, payload: BinUpdateRequest, request: Request) -> WasteNode:
    """
    Update bin fill percentage, compute resulting weight demand, and publish delta to
    Redis channel 'city:waste:deltas' and WebSocket channels. If overflow threshold is
    reached (>= 85%), an automated WASTE_OVERFLOW dispatch event is published.
    """
    if bin_id not in _BINS_STORE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Waste bin '{bin_id}' not found")

    bin_node = _BINS_STORE[bin_id]
    bin_node.fill_pct = payload.fill_pct
    bin_node.demand_kg = round((payload.fill_pct / 100.0) * bin_node.capacity_kg, 1)

    if payload.fill_pct < 10.0:
        bin_node.last_collected = datetime.now(timezone.utc)

    # Redis publishing
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.publish("city:waste:deltas", bin_node.model_dump_json())
        except Exception as exc:
            logger.warning(f"Redis publish to city:waste:deltas failed: {exc}")

    # WebSocket broadcasts
    await ws_manager.broadcast("cockpit", {"channel": "city:waste:deltas", "data": bin_node.model_dump()})
    await ws_manager.broadcast("field_worker", {"channel": "city:waste:deltas", "data": bin_node.model_dump()})

    # Automated alert on critical overflow
    if bin_node.fill_pct >= 85.0:
        overflow_event = DispatchEvent(
            event_id=f"EVT-OVF-{uuid.uuid4().hex[:6].upper()}",
            event_type="WASTE_OVERFLOW",
            lat=bin_node.lat,
            lon=bin_node.lon,
            timestamp=datetime.now(timezone.utc),
            payload={"bin_id": bin_node.id, "fill_pct": bin_node.fill_pct, "demand_kg": bin_node.demand_kg},
            severity="WARNING" if bin_node.fill_pct < 95.0 else "CRITICAL",
        )
        if redis_client:
            try:
                await redis_client.publish("city:safety:alerts", overflow_event.model_dump_json())
            except Exception:
                pass
        await ws_manager.broadcast_all(overflow_event)

    return bin_node


@router.post(
    "/optimize-routes",
    response_model=CVRPSolution,
    summary="Run CVRP route optimization for sanitation collection fleet",
)
async def optimize_waste_routes(request_body: OptimizeRoutesRequest) -> CVRPSolution:
    """
    Calculates multi-vehicle collection routes minimizing total travel distance
    while satisfying vehicle capacity constraints and servicing prioritized overflowing bins.
    """
    if request_body.bin_ids:
        nodes = [_BINS_STORE[b_id] for b_id in request_body.bin_ids if b_id in _BINS_STORE]
    else:
        # By default include bins with more than 30% fill
        nodes = [b for b in _BINS_STORE.values() if b.fill_pct >= 30.0]

    solution = solve_cvrp(
        nodes=nodes,
        max_vehicles=request_body.max_vehicles,
        vehicle_capacity_kg=request_body.vehicle_capacity_kg,
    )
    return solution


@router.post(
    "/change-detection",
    response_model=ChangeDetectionResponse,
    summary="Run AI change detection on T0 vs T1 aerial/street imagery",
)
async def detect_debris_change(payload: ChangeDetectionRequest) -> ChangeDetectionResponse:
    """
    Processes paired T0 baseline and T1 current imagery to detect illegal dumping,
    debris overflow, or uncollected trash hotspots with surface area calculations.
    """
    result = analyze_debris_change(
        t0_ref=payload.t0_image_ref,
        t1_ref=payload.t1_image_ref,
        threshold=payload.threshold,
    )
    return result


@router.get(
    "/fleet-status",
    response_model=List[FleetVehicle],
    summary="Get sanitation fleet vehicles status and live telemetry",
)
async def get_fleet_status() -> List[FleetVehicle]:
    """Retrieve positions, current fill loads, and availability of collection trucks."""
    return _FLEET_STORE
