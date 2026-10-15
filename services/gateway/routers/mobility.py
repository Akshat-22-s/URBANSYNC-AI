"""
UrbanSync AI - Mobility Router.
Handles SILN smart trip planning, dynamic departure buffers, real-time reroute analysis,
green wave synchronization, and turn-by-turn route navigation.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from ..models import (
    Coordinate,
    DynamicBuffer,
    GreenWaveCorridor,
    NavigateRequest,
    RerouteCheckRequest,
    RerouteRecommendation,
    RouteInfo,
    TripPlanCalculation,
    TripPlanRequest,
    UrgencyState,
)

logger = logging.getLogger("gateway.mobility")

router = APIRouter(prefix="/api/mobility", tags=["Mobility"])


# ============================================================================
# Engine Integration & Graceful Standalone Fallbacks
# ============================================================================

def _haversine_distance_km(c1: Coordinate, c2: Coordinate) -> float:
    """Compute Great Circle distance between two points in kilometers."""
    radius_km = 6371.0088
    dlat = math.radians(c2.lat - c1.lat)
    dlon = math.radians(c2.lon - c1.lon)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(c1.lat))
        * math.cos(math.radians(c2.lat))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return max(0.05, radius_km * c)


try:
    from services.engine_mobility.siln_calculator import calculate_departure as engine_calculate_departure
    from services.engine_mobility.green_wave import compute_green_wave as engine_compute_green_wave
    ENGINE_MOBILITY_AVAILABLE = True
except ImportError:
    engine_calculate_departure = None
    engine_compute_green_wave = None
    ENGINE_MOBILITY_AVAILABLE = False
    logger.info("Engine services.engine_mobility not found or incomplete. Using standalone fallback calculator.")


def calculate_siln_trip_plan(
    origin: Coordinate,
    destination: Coordinate,
    event_time: datetime,
    vehicle_type: str = "car",
) -> TripPlanCalculation:
    """Calculate trip plan using engine if available or standalone fallback."""
    dist_km = _haversine_distance_km(origin, destination)
    speed_map = {"car": 28.0, "transit": 20.0, "walk": 4.8, "cycling": 14.0}
    speed_kph = speed_map.get(vehicle_type.lower(), 28.0)
    transit_duration_min = round(max(3.0, (dist_km / speed_kph) * 60.0), 1)

    parking_buffer = 6.0 if dist_km > 3.0 else 3.0
    toll_buffer = 2.5 if dist_km > 12.0 else 0.0
    weather_buffer = 2.0

    if ENGINE_MOBILITY_AVAILABLE and engine_calculate_departure is not None:
        try:
            res = engine_calculate_departure(
                event_time=event_time,
                transit_duration_min=transit_duration_min,
                parking_min=parking_buffer,
                toll_min=toll_buffer,
                weather_min=weather_buffer,
            )
            # Map result to TripPlanCalculation
            buf = res["dynamic_buffer"]
            buffer_obj = DynamicBuffer(
                parking_min=buf["parking_min"],
                toll_min=buf["toll_min"],
                weather_min=buf["weather_min"],
                total=buf["total"],
            )
            urgency_enum = UrgencyState(res["urgency"]) if res["urgency"] in UrgencyState._value2member_map_ else UrgencyState.PLENTY_OF_TIME
            return TripPlanCalculation(
                event_time=res["event_time"] if isinstance(res["event_time"], datetime) else datetime.fromisoformat(res["event_time"]),
                arrive_by=res["arrive_by"] if isinstance(res["arrive_by"], datetime) else datetime.fromisoformat(res["arrive_by"]),
                transit_duration_min=res["transit_duration_min"],
                dynamic_buffer=buffer_obj,
                depart_at=res["depart_at"] if isinstance(res["depart_at"], datetime) else datetime.fromisoformat(res["depart_at"]),
                urgency=urgency_enum,
            )
        except Exception as exc:
            logger.warning(f"Engine calculate_departure error: {exc}. Falling back to standalone solver.")

    # Standalone calculation
    total_buffer = parking_buffer + toll_buffer + weather_buffer
    buffer_obj = DynamicBuffer(
        parking_min=parking_buffer,
        toll_min=toll_buffer,
        weather_min=weather_buffer,
        total=round(total_buffer, 1),
    )
    arrive_by = event_time - timedelta(minutes=buffer_obj.total)
    depart_at = arrive_by - timedelta(minutes=transit_duration_min)

    now = datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        now = datetime.now()

    diff_to_depart = (depart_at - now).total_seconds() / 60.0
    if now > arrive_by:
        urgency = UrgencyState.LATE
    elif diff_to_depart <= 0.0:
        urgency = UrgencyState.LEAVE_NOW
    elif diff_to_depart <= 15.0:
        urgency = UrgencyState.LEAVE_SOON
    else:
        urgency = UrgencyState.PLENTY_OF_TIME

    return TripPlanCalculation(
        event_time=event_time,
        arrive_by=arrive_by,
        transit_duration_min=transit_duration_min,
        dynamic_buffer=buffer_obj,
        depart_at=depart_at,
        urgency=urgency,
    )


def evaluate_reroute(
    current_delay_min: float,
    current_eta_min: float,
    detour_eta_min: float,
    route_id: Optional[str] = None,
) -> RerouteRecommendation:
    """Evaluate if detouring saves net time."""
    total_current_min = current_eta_min + current_delay_min
    time_saved = total_current_min - detour_eta_min

    if time_saved >= 2.5:
        return RerouteRecommendation(
            beneficial=True,
            time_saved_min=round(time_saved, 1),
            recommended_action="REROUTE",
            reason=f"Detour bypasses bottleneck and saves {time_saved:.1f} mins.",
            detour_route_id=f"REROUTE-{uuid.uuid4().hex[:6].upper()}",
        )
    else:
        return RerouteRecommendation(
            beneficial=False,
            time_saved_min=round(max(0.0, time_saved), 1),
            recommended_action="STAY_ON_ROUTE",
            reason=f"Detour time savings ({time_saved:.1f} min) do not exceed rerouting overhead threshold.",
            detour_route_id=None,
        )


def get_active_green_corridors() -> List[GreenWaveCorridor]:
    """Return predefined urban green wave synchronized corridors."""
    return [
        GreenWaveCorridor(
            corridor_id="GW-CORRIDOR-ALPHA",
            intersections=["INT-101-CENTRAL", "INT-102-PARKWAY", "INT-103-HOSPITAL", "INT-104-EXPRESS"],
            speed_kph=50.0,
            phase_offset_ms=[0, 4500, 9200, 14000],
        ),
        GreenWaveCorridor(
            corridor_id="GW-CORRIDOR-BETA",
            intersections=["INT-201-TECHPARK", "INT-202-METRO", "INT-203-NORTH-GATE"],
            speed_kph=45.0,
            phase_offset_ms=[0, 6000, 12500],
        ),
        GreenWaveCorridor(
            corridor_id="GW-CORRIDOR-EMERGENCY",
            intersections=["INT-301-TRAUMA-CTR", "INT-302-SOUTH-BLVD", "INT-303-BYPASS"],
            speed_kph=60.0,
            phase_offset_ms=[0, 3800, 7600],
        ),
    ]



# Default reference city coordinate (e.g., Central Hub)
DEFAULT_CITY_CENTER = Coordinate(lat=12.9716, lon=77.5946)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/trip-plan",
    response_model=TripPlanCalculation,
    summary="Calculate smart trip departure and dynamic buffer (SILN)",
)
async def calculate_trip_plan(request_body: TripPlanRequest) -> TripPlanCalculation:
    """
    Accepts destination coordinates and appointment event_time.
    Computes precise transit duration, multi-factor dynamic buffer (parking, tolls, weather),
    optimal depart_at timestamp, and urgency classification.
    """
    origin = request_body.origin or DEFAULT_CITY_CENTER
    result = calculate_siln_trip_plan(
        origin=origin,
        destination=request_body.destination,
        event_time=request_body.event_time,
        vehicle_type=request_body.vehicle_type or "car",
    )
    return result


@router.post(
    "/reroute-check",
    response_model=RerouteRecommendation,
    summary="Check if dynamic detour is beneficial",
)
async def check_reroute(payload: RerouteCheckRequest) -> RerouteRecommendation:
    """
    Evaluates current detected delay against detour travel time.
    Recommends REROUTE or STAY_ON_ROUTE based on time saved vs diversion friction.
    """
    recommendation = evaluate_reroute(
        current_delay_min=payload.current_delay_min,
        current_eta_min=payload.current_eta_min,
        detour_eta_min=payload.detour_eta_min,
        route_id=payload.route_id,
    )
    return recommendation


@router.get(
    "/green-corridors",
    response_model=List[GreenWaveCorridor],
    summary="List active synchronized green wave corridors",
)
async def list_green_corridors() -> List[GreenWaveCorridor]:
    """Retrieve all operational green wave corridors with intersection offsets and target speeds."""
    return get_active_green_corridors()


@router.post(
    "/navigate",
    response_model=RouteInfo,
    summary="Calculate turn-by-turn route waypoints and telemetry",
)
async def navigate_route(request_body: NavigateRequest) -> RouteInfo:
    """
    Computes road geometry waypoints, total distance, estimated travel time,
    and cockpit styling parameters for a requested origin and destination.
    """
    origin = request_body.origin
    dest = request_body.destination
    dist_km = _haversine_distance_km(origin, dest)

    # Generate synthetic realistic multi-point waypoint path
    steps = 6
    waypoints: List[Coordinate] = []
    for i in range(steps + 1):
        fraction = i / float(steps)
        # Apply a slight organic curve to simulate street grid
        offset = 0.0015 * math.sin(fraction * math.pi)
        lat = origin.lat + (dest.lat - origin.lat) * fraction + offset
        lon = origin.lon + (dest.lon - origin.lon) * fraction - offset
        waypoints.append(Coordinate(lat=round(lat, 6), lon=round(lon, 6)))

    duration_min = round(max(2.0, (dist_km / 30.0) * 60.0), 1)

    return RouteInfo(
        route_id=f"NAV-{uuid.uuid4().hex[:8].upper()}",
        waypoints=waypoints,
        distance_km=round(dist_km, 2),
        duration_min=duration_min,
        safety_score=0.91,
        color_hex="#06B6D4",
    )
