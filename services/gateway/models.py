"""
UrbanSync AI - Central API Gateway Shared Pydantic Models.
Defines core domain models for mobility, safety, sanitation, and dispatch services.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class UrgencyState(str, Enum):
    """Urgency states for trip planning and departure warnings."""
    PLENTY_OF_TIME = "PLENTY_OF_TIME"
    LEAVE_SOON = "LEAVE_SOON"
    LEAVE_NOW = "LEAVE_NOW"
    LATE = "LATE"


class SurveillanceStatus(str, Enum):
    """Surveillance coverage status along a corridor or location."""
    SURVEILLANCE_LOCKED = "SURVEILLANCE_LOCKED"
    BLIND_SPOT_DETECTED = "BLIND_SPOT_DETECTED"
    OUT_OF_RANGE = "OUT_OF_RANGE"


class PinType(str, Enum):
    """Escort PIN type: SAFE pin dismisses escort, DURESS pin triggers silent red alert."""
    SAFE = "SAFE"
    DURESS = "DURESS"


class EscalationCode(str, Enum):
    """Emergency escalation codes."""
    CODE_GREEN = "CODE_GREEN"
    CODE_RED_P1 = "CODE_RED_P1"


# ============================================================================
# Core Domain Models
# ============================================================================

class Coordinate(BaseModel):
    """Geographic coordinate representation."""
    lat: float = Field(..., description="Latitude in decimal degrees", ge=-90.0, le=90.0)
    lon: float = Field(..., description="Longitude in decimal degrees", ge=-180.0, le=180.0)


class WasteNode(BaseModel):
    """Smart waste container or collection point."""
    id: str = Field(..., description="Unique bin or node identifier")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    fill_pct: float = Field(ge=0.0, le=100.0, description="Fill level percentage (0-100%)")
    capacity_kg: float = Field(default=5000.0, description="Total container capacity in kilograms")
    demand_kg: float = Field(default=0.0, description="Current weight demand to be collected in kg")
    last_collected: Optional[datetime] = Field(default=None, description="Timestamp of last collection")


class DynamicBuffer(BaseModel):
    """Dynamic buffer times calculated based on real-time city conditions."""
    parking_min: float = Field(default=5.0, description="Estimated parking search time in minutes")
    toll_min: float = Field(default=0.0, description="Estimated toll gate queuing time in minutes")
    weather_min: float = Field(default=0.0, description="Weather-induced delay penalty in minutes")
    total: float = Field(default=5.0, description="Sum of all dynamic buffer components in minutes")


class TripPlanCalculation(BaseModel):
    """Complete trip planning calculation output from SILN engine."""
    event_time: datetime = Field(..., description="Scheduled appointment or event timestamp")
    arrive_by: datetime = Field(..., description="Target arrival timestamp accounting for buffer")
    transit_duration_min: float = Field(..., description="Pure transit duration in minutes")
    dynamic_buffer: DynamicBuffer = Field(..., description="Dynamic buffer components breakdown")
    depart_at: datetime = Field(..., description="Recommended departure timestamp")
    urgency: UrgencyState = Field(..., description="Urgency categorization relative to current time")


class RouteInfo(BaseModel):
    """Route navigation geometry and telemetry summary."""
    route_id: str = Field(..., description="Unique route identifier")
    waypoints: list[Coordinate] = Field(default_factory=list, description="Ordered coordinate waypoints")
    distance_km: float = Field(..., description="Route distance in kilometers")
    duration_min: float = Field(..., description="Estimated travel duration in minutes")
    safety_score: Optional[float] = Field(default=None, description="Composite safety score (0.0 to 1.0)")
    color_hex: str = Field(default="#06B6D4", description="Hex color code for rendering on cockpit map")


class SafePathResult(BaseModel):
    """Dual-path safety calculation comparing fastest vs safest pedestrian corridors."""
    route_a: RouteInfo = Field(..., description="Fastest / direct path (e.g., Crimson #F43F5E)")
    route_b: RouteInfo = Field(..., description="Safest path with maximum CCTV coverage (Emerald #10B981)")
    surveillance_status: SurveillanceStatus = Field(..., description="Overall surveillance lock status")
    blind_spots: list[Coordinate] = Field(default_factory=list, description="Coordinates of identified blind spots")


class CitizenTelemetryPacket(BaseModel):
    """High-frequency telemetry stream from citizen companion app."""
    citizen_id: str = Field(..., description="Citizen device/user identifier")
    lat: float = Field(..., description="Current latitude")
    lon: float = Field(..., description="Current longitude")
    accel_g: float = Field(default=0.0, description="Current accelerometer jerk/force in Gs")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of telemetry")
    escort_active: bool = Field(default=False, description="Whether dead-man escort mode is currently active")
    heading_deg: float = Field(default=0.0, description="Compass heading in degrees (0-360)")


class EmergencyEscalationPayload(BaseModel):
    """Emergency alert payload broadcast during critical events."""
    citizen_id: str = Field(..., description="Identifier of the citizen or sensor")
    lat: float = Field(..., description="Latitude of the emergency incident")
    lon: float = Field(..., description="Longitude of the emergency incident")
    pin_type: PinType = Field(..., description="PIN type used: SAFE or DURESS")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Incident timestamp")
    code: EscalationCode = Field(..., description="Escalation urgency code: CODE_GREEN or CODE_RED_P1")


class CVRPSolution(BaseModel):
    """Capacitated Vehicle Routing Problem (CVRP) route optimization solution."""
    vehicle_routes: list[list[str]] = Field(..., description="List of routes as ordered bin/node IDs per vehicle")
    total_distance_km: float = Field(..., description="Total fleet distance in kilometers")
    total_demand_served_kg: float = Field(..., description="Total waste demand collected in kilograms")


class GreenWaveCorridor(BaseModel):
    """Dynamic green wave synchronized corridor for emergency or transit vehicles."""
    corridor_id: str = Field(..., description="Corridor identifier")
    intersections: list[str] = Field(..., description="Ordered intersection IDs along corridor")
    speed_kph: float = Field(..., description="Target progression speed in km/h")
    phase_offset_ms: list[int] = Field(..., description="Offset in milliseconds per intersection for green wave")


class DispatchEvent(BaseModel):
    """Central dispatch event log entry and real-time broadcast model."""
    event_id: str = Field(..., description="Unique event identifier (e.g., UUID)")
    event_type: str = Field(
        ...,
        description="Event classification (WASTE_OVERFLOW | SNATCH_ALERT | DURESS_TRIGGER | VEHICLE_REROUTE | SYSTEM_ALERT)"
    )
    lat: float = Field(..., description="Latitude of event location")
    lon: float = Field(..., description="Longitude of event location")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event creation timestamp")
    payload: dict[str, Any] = Field(default_factory=dict, description="Arbitrary context payload")
    severity: str = Field(default="INFO", description="Severity level: INFO | WARNING | CRITICAL")


# ============================================================================
# Additional Request / Response Models
# ============================================================================

class TripPlanRequest(BaseModel):
    """Request payload for trip planning."""
    destination: Coordinate = Field(..., description="Target destination coordinates")
    event_time: datetime = Field(..., description="Event start timestamp")
    origin: Optional[Coordinate] = Field(default=None, description="Optional starting coordinates (defaults to city center)")
    vehicle_type: Optional[str] = Field(default="car", description="Mode of transport: car | transit | walk")


class RerouteCheckRequest(BaseModel):
    """Request payload for evaluating route detour vs current delay."""
    current_delay_min: float = Field(..., description="Current detected delay in minutes on existing route")
    current_eta_min: float = Field(..., description="Remaining travel time on current route without additional detour")
    detour_eta_min: float = Field(..., description="Estimated travel time if rerouting through alternative path")
    route_id: Optional[str] = Field(default=None, description="Current route identifier")


class RerouteRecommendation(BaseModel):
    """Recommendation output for route diversion."""
    beneficial: bool = Field(..., description="True if reroute saves net travel time")
    time_saved_min: float = Field(..., description="Net minutes saved by rerouting")
    recommended_action: str = Field(..., description="Action: REROUTE or STAY_ON_ROUTE")
    reason: str = Field(..., description="Descriptive explanation of decision")
    detour_route_id: Optional[str] = Field(default=None, description="Alternative route ID if rerouting is beneficial")


class NavigateRequest(BaseModel):
    """Request payload for calculating route waypoints."""
    origin: Coordinate = Field(..., description="Starting coordinate")
    destination: Coordinate = Field(..., description="Destination coordinate")
    mode: Optional[str] = Field(default="driving", description="Navigation mode: driving | walking | cycling")


class BinUpdateRequest(BaseModel):
    """Request payload to update a waste node fill percentage."""
    fill_pct: float = Field(..., ge=0.0, le=100.0, description="New fill percentage (0 to 100)")


class OptimizeRoutesRequest(BaseModel):
    """Request payload to trigger CVRP waste route optimization."""
    bin_ids: Optional[list[str]] = Field(default=None, description="Optional subset of bin IDs to route")
    max_vehicles: int = Field(default=3, ge=1, le=20, description="Number of collection vehicles available")
    vehicle_capacity_kg: float = Field(default=5000.0, ge=100.0, description="Maximum load capacity per vehicle in kg")


class ChangeDetectionRequest(BaseModel):
    """Request payload for AI aerial/street debris change detection."""
    t0_image_ref: str = Field(..., description="Baseline image URL or storage reference at T0")
    t1_image_ref: str = Field(..., description="Current image URL or storage reference at T1")
    location: Optional[Coordinate] = Field(default=None, description="Geographic location of image capture")
    threshold: float = Field(default=0.2, ge=0.0, le=1.0, description="Sensitivity threshold for delta detection")


class ChangeDetectionResponse(BaseModel):
    """Response payload for aerial debris change detection."""
    delta_detected: bool = Field(..., description="True if significant debris accumulation or change was detected")
    debris_area_sqm: float = Field(..., description="Estimated surface area of debris in square meters")
    confidence: float = Field(..., description="AI model confidence score (0.0 to 1.0)")
    severity: str = Field(..., description="Debris severity classification: LOW | MEDIUM | HIGH | CRITICAL")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional segmentation and telemetry metadata")


class FleetVehicle(BaseModel):
    """Sanitation fleet vehicle status model."""
    vehicle_id: str = Field(..., description="Unique vehicle ID")
    lat: float = Field(..., description="Current latitude")
    lon: float = Field(..., description="Current longitude")
    capacity_kg: float = Field(default=5000.0, description="Maximum capacity in kg")
    current_load_kg: float = Field(default=0.0, description="Current load in kg")
    status: str = Field(default="AVAILABLE", description="Vehicle status: AVAILABLE | IN_ROUTE | MAINTENANCE")


class SafePathRequest(BaseModel):
    """Request payload for calculating dual SafePath routes."""
    origin: Coordinate = Field(..., description="Trip origin coordinates")
    destination: Coordinate = Field(..., description="Trip destination coordinates")


class EscortStartRequest(BaseModel):
    """Request payload to initiate a dead-man digital safety escort."""
    citizen_id: str = Field(..., description="Citizen identifier")
    origin: Coordinate = Field(..., description="Starting coordinates")
    destination: Coordinate = Field(..., description="Destination coordinates")
    initial_pin: Optional[str] = Field(default="1234", description="Expected safe pin (defaults to 1234)")


class EscortSession(BaseModel):
    """Active dead-man escort session details."""
    session_id: str = Field(..., description="Unique escort session ID")
    citizen_id: str = Field(..., description="Citizen identifier")
    status: str = Field(default="ACTIVE", description="Session status: ACTIVE | COMPLETED | DURESS | ESCALATED")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Start timestamp")
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last received heartbeat")
    origin: Coordinate = Field(..., description="Origin coordinates")
    destination: Coordinate = Field(..., description="Target destination coordinates")
    escort_active: bool = Field(default=True, description="Whether escort monitoring is ongoing")


class HeartbeatResponse(BaseModel):
    """Response payload acknowledging escort telemetry heartbeat."""
    citizen_id: str = Field(..., description="Citizen identifier")
    status: str = Field(..., description="Status string: OK | ALERT_TRIGGERED")
    jerk_detected: bool = Field(..., description="True if sudden acceleration exceeded threshold")
    accel_g: float = Field(..., description="Processed acceleration in Gs")
    threshold_exceeded: bool = Field(..., description="Whether threshold of > 3.0g was exceeded")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Processing timestamp")
    message: str = Field(..., description="Status summary message")


class PinVerificationRequest(BaseModel):
    """Request payload to submit PIN during an active escort or duress event."""
    citizen_id: str = Field(..., description="Citizen identifier")
    pin: str = Field(..., description="Entered 4-digit security PIN")


class PinVerificationResponse(BaseModel):
    """Response payload for escort PIN verification."""
    verified: bool = Field(..., description="Whether PIN is a recognized valid PIN")
    pin_type: PinType = Field(..., description="Classified PIN type: SAFE or DURESS")
    action_taken: str = Field(..., description="System response action taken")
    escalation_triggered: bool = Field(..., description="Whether emergency escalation was initiated")
    message: str = Field(..., description="Human-readable response message")


class SurveillanceStatusResponse(BaseModel):
    """Surveillance coverage details for a given coordinate or corridor."""
    lat: float = Field(..., description="Latitude assessed")
    lon: float = Field(..., description="Longitude assessed")
    status: SurveillanceStatus = Field(..., description="Surveillance lock evaluation")
    active_cameras: int = Field(..., description="Number of active cameras covering this zone")
    blind_spot_risk: float = Field(..., description="Normalized blind spot risk factor (0.0 to 1.0)")
    last_assessment: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of evaluation")
