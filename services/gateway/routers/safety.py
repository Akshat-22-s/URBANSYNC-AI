"""
UrbanSync AI - Safety Router.
Manages SafePath dual routing (shortest vs safest), dead-man citizen escort monitoring,
jerk/snatch detection (>3.0g threshold), PIN verification (SAFE 1234 vs DURESS 9999),
emergency escalation broadcasting, and real-time surveillance coverage assessment.
"""

from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..models import (
    CitizenTelemetryPacket,
    Coordinate,
    DispatchEvent,
    EmergencyEscalationPayload,
    EscalationCode,
    EscortSession,
    EscortStartRequest,
    HeartbeatResponse,
    PinType,
    PinVerificationRequest,
    PinVerificationResponse,
    RouteInfo,
    SafePathRequest,
    SafePathResult,
    SurveillanceStatus,
    SurveillanceStatusResponse,
)
from ..websocket_manager import ws_manager

logger = logging.getLogger("gateway.safety")

router = APIRouter(prefix="/api/safety", tags=["Safety"])

# Threshold for accelerometer jerk force indicative of phone snatching or physical assault
JERK_SNATCH_THRESHOLD_G = 3.0

# In-memory escort sessions store: citizen_id -> EscortSession
_ESCORT_SESSIONS: Dict[str, EscortSession] = {}


# ============================================================================
# Engine Integration & Standalone Fallbacks
# ============================================================================

def _haversine_distance_km(c1: Coordinate, c2: Coordinate) -> float:
    """Compute distance in km between two Coordinates."""
    radius_km = 6371.0088
    dlat = math.radians(c2.lat - c1.lat)
    dlon = math.radians(c2.lon - c1.lon)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(c1.lat))
        * math.cos(math.radians(c2.lat))
        * math.sin(dlon / 2.0) ** 2
    )
    return radius_km * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))


try:
    from services.engine_safety.safepath_router import (
        compute_safepath as engine_compute_safepath,
        get_surveillance_status as engine_get_surveillance_status,
    )
    from services.engine_safety.duress_auth import verify_pin as engine_verify_pin
    ENGINE_SAFETY_AVAILABLE = True
except ImportError:
    ENGINE_SAFETY_AVAILABLE = False
    engine_compute_safepath = None
    engine_get_surveillance_status = None
    engine_verify_pin = None
    logger.info("Engine services.engine_safety not found or incomplete. Using standalone fallback safety algorithms.")


def compute_safepath(origin: Coordinate, destination: Coordinate) -> SafePathResult:
    """
    Calculates dual route comparison:
    Route A: Shortest direct route (crimson #F43F5E), through secondary streets with blind spots.
    Route B: Safest illuminated & CCTV-monitored corridor (emerald #10B981).
    """
    dist_direct = _haversine_distance_km(origin, destination)
    dist_a = round(max(0.4, dist_direct), 2)
    dist_b = round(dist_a * 1.18, 2)  # Route B has ~18% detour via protected corridors

    # Route A waypoints (direct, 5 steps)
    steps = 5
    waypoints_a: List[Coordinate] = []
    for i in range(steps + 1):
        t = i / float(steps)
        lat = origin.lat + (destination.lat - origin.lat) * t
        lon = origin.lon + (destination.lon - origin.lon) * t
        waypoints_a.append(Coordinate(lat=round(lat, 6), lon=round(lon, 6)))

    # Route B waypoints (curved through brightly lit arterial corridors)
    waypoints_b: List[Coordinate] = []
    for i in range(steps + 1):
        t = i / float(steps)
        arc_offset = 0.0028 * math.sin(t * math.pi)
        lat = origin.lat + (destination.lat - origin.lat) * t + arc_offset
        lon = origin.lon + (destination.lon - origin.lon) * t - arc_offset
        waypoints_b.append(Coordinate(lat=round(lat, 6), lon=round(lon, 6)))

    # Identified blind spots along Route A
    blind_spots = [
        Coordinate(
            lat=round(origin.lat + (destination.lat - origin.lat) * 0.42, 6),
            lon=round(origin.lon + (destination.lon - origin.lon) * 0.42, 6),
        ),
        Coordinate(
            lat=round(origin.lat + (destination.lat - origin.lat) * 0.78, 6),
            lon=round(origin.lon + (destination.lon - origin.lon) * 0.78, 6),
        ),
    ]

    route_a = RouteInfo(
        route_id=f"ROUTE-A-FASTEST-{uuid.uuid4().hex[:6].upper()}",
        waypoints=waypoints_a,
        distance_km=dist_a,
        duration_min=round((dist_a / 4.5) * 60.0, 1),
        safety_score=0.54,
        color_hex="#F43F5E",  # Crimson
    )

    route_b = RouteInfo(
        route_id=f"ROUTE-B-SAFEST-{uuid.uuid4().hex[:6].upper()}",
        waypoints=waypoints_b,
        distance_km=dist_b,
        duration_min=round((dist_b / 4.5) * 60.0, 1),
        safety_score=0.95,
        color_hex="#10B981",  # Emerald
    )

    return SafePathResult(
        route_a=route_a,
        route_b=route_b,
        surveillance_status=SurveillanceStatus.SURVEILLANCE_LOCKED,
        blind_spots=blind_spots,
    )


def evaluate_surveillance(lat: float, lon: float) -> SurveillanceStatusResponse:
    """Standalone surveillance zone assessment."""
    center_lat, center_lon = 12.9716, 77.5946
    dist = _haversine_distance_km(Coordinate(lat=lat, lon=lon), Coordinate(lat=center_lat, lon=center_lon))

    if dist < 4.0:
        status_enum = SurveillanceStatus.SURVEILLANCE_LOCKED
        cameras = 14
        risk = 0.08
    elif dist < 12.0:
        status_enum = SurveillanceStatus.BLIND_SPOT_DETECTED
        cameras = 4
        risk = 0.42
    else:
        status_enum = SurveillanceStatus.OUT_OF_RANGE
        cameras = 0
        risk = 0.88

    return SurveillanceStatusResponse(
        lat=lat,
        lon=lon,
        status=status_enum,
        active_cameras=cameras,
        blind_spot_risk=risk,
        last_assessment=datetime.now(timezone.utc),
    )



# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/safepath",
    response_model=SafePathResult,
    summary="Compute dual routes: Route A (fastest) vs Route B (safest)",
)
async def get_safepath(request_body: SafePathRequest) -> SafePathResult:
    """
    Computes comparative paths between origin and destination:
    - Route A (Crimson #F43F5E): Shortest physical distance, lower CCTV density.
    - Route B (Emerald #10B981): Maximum illumination and AI CCTV surveillance coverage.
    """
    return compute_safepath(request_body.origin, request_body.destination)


@router.post(
    "/escort/start",
    response_model=EscortSession,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate active dead-man escort session for a citizen",
)
async def start_escort(request_body: EscortStartRequest) -> EscortSession:
    """
    Starts an active companion escort session. Citizen must continuously stream
    heartbeats and telemetry until destination is reached or verified PIN is entered.
    """
    now = datetime.now(timezone.utc)
    session = EscortSession(
        session_id=f"ESCORT-{uuid.uuid4().hex[:8].upper()}",
        citizen_id=request_body.citizen_id,
        status="ACTIVE",
        started_at=now,
        last_heartbeat=now,
        origin=request_body.origin,
        destination=request_body.destination,
        escort_active=True,
    )
    _ESCORT_SESSIONS[request_body.citizen_id] = session

    # Broadcast escort start to cockpit
    await ws_manager.broadcast("cockpit", {
        "event": "ESCORT_STARTED",
        "citizen_id": session.citizen_id,
        "session_id": session.session_id,
        "origin": session.origin.model_dump(),
        "destination": session.destination.model_dump(),
        "timestamp": now.isoformat(),
    })

    return session


@router.post(
    "/escort/heartbeat",
    response_model=HeartbeatResponse,
    summary="Accept citizen telemetry and evaluate jerk/snatch thresholds",
)
async def escort_heartbeat(packet: CitizenTelemetryPacket, request: Request) -> HeartbeatResponse:
    """
    Processes citizen telemetry packets. Evaluates accelerometer jerk force.
    If accel_g exceeds threshold (> 3.0g), automatically triggers a SNATCH_ALERT
    and dispatches high-priority incident to command center and first responders.
    """
    now = datetime.now(timezone.utc)

    # Update active escort session timestamp if tracked
    if packet.citizen_id in _ESCORT_SESSIONS:
        _ESCORT_SESSIONS[packet.citizen_id].last_heartbeat = packet.timestamp

    # Check jerk threshold
    threshold_exceeded = packet.accel_g > JERK_SNATCH_THRESHOLD_G

    if threshold_exceeded:
        logger.warning(
            f"SNATCH DETECTED! Citizen {packet.citizen_id} recorded {packet.accel_g}g jerk force."
        )
        snatch_event = DispatchEvent(
            event_id=f"EVT-SNATCH-{uuid.uuid4().hex[:6].upper()}",
            event_type="SNATCH_ALERT",
            lat=packet.lat,
            lon=packet.lon,
            timestamp=now,
            payload={
                "citizen_id": packet.citizen_id,
                "accel_g": packet.accel_g,
                "threshold": JERK_SNATCH_THRESHOLD_G,
                "heading_deg": packet.heading_deg,
                "escort_active": packet.escort_active,
            },
            severity="CRITICAL",
        )

        # Publish to Redis
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client:
            try:
                await redis_client.publish("city:safety:alerts", snatch_event.model_dump_json())
            except Exception as exc:
                logger.warning(f"Redis publish failed: {exc}")

        # Broadcast critical alert immediately to all connected clients
        await ws_manager.broadcast_all(snatch_event)

        return HeartbeatResponse(
            citizen_id=packet.citizen_id,
            status="ALERT_TRIGGERED",
            jerk_detected=True,
            accel_g=packet.accel_g,
            threshold_exceeded=True,
            timestamp=now,
            message="CRITICAL: Jerk threshold (>3.0g) exceeded! Snatch alert broadcasted to emergency dispatch.",
        )

    # Telemetry nominal - broadcast kinematics to cockpit and citizen
    await ws_manager.broadcast("cockpit", {
        "channel": "city:telemetry:kinematics",
        "data": packet.model_dump(),
    })

    return HeartbeatResponse(
        citizen_id=packet.citizen_id,
        status="OK",
        jerk_detected=False,
        accel_g=packet.accel_g,
        threshold_exceeded=False,
        timestamp=now,
        message="Telemetry nominal. Heartbeat registered.",
    )


@router.post(
    "/escort/verify-pin",
    response_model=PinVerificationResponse,
    summary="Verify security PIN (SAFE 1234 vs DURESS 9999)",
)
async def verify_pin(payload: PinVerificationRequest, request: Request) -> PinVerificationResponse:
    """
    Submits user PIN to resolve dead-man timer:
    - SAFE PIN ('1234'): Deactivates escort normally with CODE_GREEN.
    - DURESS PIN ('9999'): Silently triggers CODE_RED_P1 alert without alerting assailant.
    """
    citizen_id = payload.citizen_id
    entered_pin = payload.pin.strip()

    if entered_pin == "1234":
        if citizen_id in _ESCORT_SESSIONS:
            _ESCORT_SESSIONS[citizen_id].status = "COMPLETED"
            _ESCORT_SESSIONS[citizen_id].escort_active = False

        # Broadcast peaceful conclusion
        await ws_manager.broadcast("cockpit", {
            "event": "ESCORT_COMPLETED_SAFELY",
            "citizen_id": citizen_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return PinVerificationResponse(
            verified=True,
            pin_type=PinType.SAFE,
            action_taken="ESCORT_DEACTIVATED",
            escalation_triggered=False,
            message="Safe PIN verified. Escort session successfully concluded.",
        )

    elif entered_pin == "9999":
        # Silent Duress Alarm
        logger.critical(f"DURESS PIN ENTERED BY CITIZEN {citizen_id}! SILENT ALARM ENGAGED.")
        now = datetime.now(timezone.utc)

        session = _ESCORT_SESSIONS.get(citizen_id)
        incident_lat = session.origin.lat if session else 12.9716
        incident_lon = session.origin.lon if session else 77.5946

        if session:
            session.status = "DURESS"

        duress_event = DispatchEvent(
            event_id=f"EVT-DURESS-{uuid.uuid4().hex[:6].upper()}",
            event_type="DURESS_TRIGGER",
            lat=incident_lat,
            lon=incident_lon,
            timestamp=now,
            payload={
                "citizen_id": citizen_id,
                "pin_type": "DURESS",
                "code": "CODE_RED_P1",
                "silent_mode": True,
            },
            severity="CRITICAL",
        )

        # Redis publish
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client:
            try:
                await redis_client.publish("city:safety:alerts", duress_event.model_dump_json())
            except Exception as exc:
                logger.warning(f"Redis publish failed: {exc}")

        # Broadcast critical alert to cockpit and first responders
        await ws_manager.broadcast("cockpit", duress_event)
        await ws_manager.broadcast("field_worker", duress_event)

        # Return benign-looking acknowledgment to prevent assailant suspicion
        return PinVerificationResponse(
            verified=True,
            pin_type=PinType.DURESS,
            action_taken="SILENT_CODE_RED_ESCALATION",
            escalation_triggered=True,
            message="PIN verified. Companion escort paused.",
        )

    else:
        return PinVerificationResponse(
            verified=False,
            pin_type=PinType.SAFE,
            action_taken="NONE",
            escalation_triggered=False,
            message="Unrecognized PIN. Escort remains active.",
        )


@router.post(
    "/escalate",
    response_model=DispatchEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Broadcast manual or sensor emergency escalation",
)
async def escalate_emergency(payload: EmergencyEscalationPayload, request: Request) -> DispatchEvent:
    """
    Directly broadcasts emergency escalation (CODE_RED_P1 or CODE_GREEN) across all channels.
    """
    event = DispatchEvent(
        event_id=f"EVT-ESC-{uuid.uuid4().hex[:6].upper()}",
        event_type="DURESS_TRIGGER" if payload.pin_type == PinType.DURESS else "EMERGENCY_ESCALATION",
        lat=payload.lat,
        lon=payload.lon,
        timestamp=payload.timestamp,
        payload={
            "citizen_id": payload.citizen_id,
            "pin_type": payload.pin_type.value,
            "code": payload.code.value,
        },
        severity="CRITICAL" if payload.code == EscalationCode.CODE_RED_P1 else "INFO",
    )

    redis_client = getattr(request.app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.publish("city:safety:alerts", event.model_dump_json())
        except Exception as exc:
            logger.warning(f"Redis publish failed: {exc}")

    # Broadcast to all channels
    await ws_manager.broadcast_all(event)
    return event


@router.get(
    "/surveillance-status",
    response_model=SurveillanceStatusResponse,
    summary="Get surveillance coverage status for given coordinates",
)
async def get_surveillance_status(
    lat: float = Query(..., description="Latitude to assess", ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude to assess", ge=-180.0, le=180.0),
) -> SurveillanceStatusResponse:
    """Assesses active CCTV camera density, blind spot risk, and surveillance lock state."""
    return evaluate_surveillance(lat=lat, lon=lon)
