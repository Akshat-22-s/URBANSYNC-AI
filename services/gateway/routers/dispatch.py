"""
UrbanSync AI - Dispatch Router.
Manages city-wide dispatch events, incident broadcasting, and alert propagation.
"""

from __future__ import annotations

import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..models import DispatchEvent
from ..websocket_manager import ws_manager

logger = logging.getLogger("gateway.dispatch")

router = APIRouter(prefix="/api/dispatch", tags=["Dispatch"])

# Engine integration with graceful fallback
try:
    from services.engine_dispatch.processor import process_dispatch_event
except ImportError:
    logger.info("Engine services.engine_dispatch not found. Using standalone fallback processor.")

    def process_dispatch_event(event: DispatchEvent) -> Dict[str, Any]:
        """Fallback rule-based event processor."""
        priority_score = 1.0
        if event.severity == "CRITICAL":
            priority_score = 10.0
        elif event.severity == "WARNING":
            priority_score = 5.0

        return {
            "processed": True,
            "priority_score": priority_score,
            "auto_dispatched": event.severity == "CRITICAL",
            "dispatch_unit": "POLICE_PATROL_104" if "SNATCH" in event.event_type or "DURESS" in event.event_type else "CITY_SERVICES",
            "estimated_response_sec": 180 if event.severity == "CRITICAL" else 900,
        }


# Bounded in-memory event log (stores up to 100 recent events)
_EVENTS_BUFFER: deque[DispatchEvent] = deque(maxlen=100)


def _seed_initial_events() -> None:
    """Pre-populate sample dispatch events for testing and cockpit demonstration."""
    now = datetime.now(timezone.utc)
    sample_events = [
        DispatchEvent(
            event_id="EVT-INIT-001",
            event_type="WASTE_OVERFLOW",
            lat=12.9716,
            lon=77.5946,
            timestamp=now,
            payload={"bin_id": "BIN-CENTRAL-01", "fill_pct": 94.2, "demand_kg": 4710.0},
            severity="WARNING",
        ),
        DispatchEvent(
            event_id="EVT-INIT-002",
            event_type="VEHICLE_REROUTE",
            lat=12.9780,
            lon=77.5980,
            timestamp=now,
            payload={"vehicle_id": "FLEET-TRUCK-02", "reason": "Severe bottleneck on MG Road", "time_saved_min": 7.5},
            severity="INFO",
        ),
        DispatchEvent(
            event_id="EVT-INIT-003",
            event_type="DURESS_TRIGGER",
            lat=12.9650,
            lon=77.5850,
            timestamp=now,
            payload={"citizen_id": "CITIZEN-9812", "pin_type": "DURESS", "code": "CODE_RED_P1", "zone": "South Corridor"},
            severity="CRITICAL",
        ),
    ]
    for ev in sample_events:
        _EVENTS_BUFFER.append(ev)


_seed_initial_events()


@router.post(
    "/events",
    response_model=DispatchEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Create and publish a new dispatch event",
)
async def create_event(event: DispatchEvent, request: Request) -> DispatchEvent:
    """
    Publish a new city dispatch event (WASTE_OVERFLOW, SNATCH_ALERT, DURESS_TRIGGER, VEHICLE_REROUTE).
    Broadcasts via Redis channel 'city:safety:alerts' and WebSocket channel 'cockpit'.
    """
    if not event.event_id:
        event.event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

    # Process event through engine or fallback
    enrichment = process_dispatch_event(event)
    event.payload = {**event.payload, **enrichment}

    # Store in memory deque
    _EVENTS_BUFFER.appendleft(event)

    # Publish to Redis if available
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.publish("city:safety:alerts", event.model_dump_json())
        except Exception as exc:
            logger.warning(f"Redis publish failed: {exc}")

    # Real-time WebSocket broadcasting
    if event.severity == "CRITICAL":
        await ws_manager.broadcast_all(event)
    else:
        await ws_manager.broadcast("cockpit", event)
        if "WASTE" in event.event_type:
            await ws_manager.broadcast("field_worker", event)

    return event


@router.get(
    "/events",
    response_model=List[DispatchEvent],
    summary="List recent dispatch events",
)
async def list_events(
    limit: int = Query(default=50, ge=1, le=100, description="Max number of events to return"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    severity: Optional[str] = Query(default=None, description="Filter by severity level"),
) -> List[DispatchEvent]:
    """Retrieve up to 100 recent dispatch events from memory, newest first."""
    results: List[DispatchEvent] = []
    for ev in _EVENTS_BUFFER:
        if event_type and ev.event_type != event_type:
            continue
        if severity and ev.severity != severity:
            continue
        results.append(ev)
        if len(results) >= limit:
            break
    return results


@router.get(
    "/events/{event_id}",
    response_model=DispatchEvent,
    summary="Get dispatch event by ID",
)
async def get_event(event_id: str) -> DispatchEvent:
    """Retrieve details for a specific dispatch event."""
    for ev in _EVENTS_BUFFER:
        if ev.event_id == event_id:
            return ev
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dispatch event '{event_id}' not found")
