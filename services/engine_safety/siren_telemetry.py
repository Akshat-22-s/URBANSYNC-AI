"""Citizen telemetry processing and jerk event detection.

Monitors accelerometer data for snatch/assault indicators:
- Jerk threshold: > 3.0g sudden acceleration
- Triggers 45-second dead-man countdown
- Processes escort heartbeats
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .occlusion_raycast import check_surveillance_status

JERK_THRESHOLD_G: float = 3.0
ESCORT_TIMEOUT_SEC: int = 45


def check_jerk_event(accel_g: float, threshold: float = JERK_THRESHOLD_G) -> bool:
    """Return True if acceleration magnitude exceeds the jerk threshold."""
    return float(accel_g) > float(threshold)


@dataclass
class EscortSession:
    """Active citizen digital escort session."""

    citizen_id: str
    started_at: datetime
    last_heartbeat: datetime
    is_active: bool
    jerk_detected: bool
    countdown_remaining_sec: int
    origin: tuple[float, float]
    destination: tuple[float, float]
    last_lat: float | None = None
    last_lon: float | None = None
    last_speed_kmh: float = 0.0
    last_heading_deg: float = 0.0
    alarm_triggered: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize escort session to dictionary."""
        return {
            "citizen_id": self.citizen_id,
            "started_at": self.started_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_active": self.is_active,
            "jerk_detected": self.jerk_detected,
            "countdown_remaining_sec": self.countdown_remaining_sec,
            "origin": self.origin,
            "destination": self.destination,
            "last_position": {"lat": self.last_lat, "lon": self.last_lon},
            "last_speed_kmh": self.last_speed_kmh,
            "last_heading_deg": self.last_heading_deg,
            "alarm_triggered": self.alarm_triggered,
        }


class EscortManager:
    """Manages citizen escort sessions, heartbeats, dead-man timers, and timeouts."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, EscortSession] = {}

    def start_escort(
        self,
        citizen_id: str,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> EscortSession:
        """Initialize or reset an active escort session for a citizen."""
        with self._lock:
            now = datetime.now(timezone.utc)
            session = EscortSession(
                citizen_id=citizen_id,
                started_at=now,
                last_heartbeat=now,
                is_active=True,
                jerk_detected=False,
                countdown_remaining_sec=ESCORT_TIMEOUT_SEC,
                origin=(origin_lat, origin_lon),
                destination=(dest_lat, dest_lon),
                last_lat=origin_lat,
                last_lon=origin_lon,
                last_speed_kmh=0.0,
                last_heading_deg=0.0,
                alarm_triggered=False,
            )
            self._sessions[citizen_id] = session
            return session

    def heartbeat(
        self,
        citizen_id: str,
        lat: float,
        lon: float,
        accel_g: float,
        speed_kmh: float = 0.0,
        heading_deg: float = 0.0,
    ) -> dict[str, Any]:
        """Process heartbeat, check jerk event, and update dead-man countdown."""
        with self._lock:
            now = datetime.now(timezone.utc)
            session = self._sessions.get(citizen_id)

            if not session:
                # Auto-initialize session if not explicitly started
                session = EscortSession(
                    citizen_id=citizen_id,
                    started_at=now,
                    last_heartbeat=now,
                    is_active=True,
                    jerk_detected=False,
                    countdown_remaining_sec=ESCORT_TIMEOUT_SEC,
                    origin=(lat, lon),
                    destination=(lat, lon),
                    last_lat=lat,
                    last_lon=lon,
                    last_speed_kmh=speed_kmh,
                    last_heading_deg=heading_deg,
                    alarm_triggered=False,
                )
                self._sessions[citizen_id] = session

            if not session.is_active:
                return {
                    "is_active": False,
                    "jerk_detected": False,
                    "countdown_remaining_sec": 0,
                    "should_trigger_alarm": False,
                    "position": {"lat": lat, "lon": lon},
                }

            elapsed_sec = max(1, int((now - session.last_heartbeat).total_seconds()))

            # Check if current reading violates jerk threshold
            is_jerk = check_jerk_event(accel_g)
            if is_jerk:
                session.jerk_detected = True

            # If jerk was triggered, decrement countdown timer
            if session.jerk_detected:
                session.countdown_remaining_sec = max(
                    0, session.countdown_remaining_sec - elapsed_sec
                )
                if session.countdown_remaining_sec <= 0:
                    session.alarm_triggered = True

            # Update session state
            session.last_heartbeat = now
            session.last_lat = lat
            session.last_lon = lon
            session.last_speed_kmh = speed_kmh
            session.last_heading_deg = heading_deg

            should_trigger = session.alarm_triggered or (
                session.jerk_detected and session.countdown_remaining_sec <= 0
            )

            return {
                "is_active": session.is_active,
                "jerk_detected": session.jerk_detected,
                "countdown_remaining_sec": session.countdown_remaining_sec,
                "should_trigger_alarm": should_trigger,
                "position": {"lat": lat, "lon": lon},
            }

    def end_escort(self, citizen_id: str, pin_verified: bool = False) -> dict[str, Any]:
        """Deactivate escort session upon nominal clearance or authorized termination."""
        with self._lock:
            session = self._sessions.get(citizen_id)
            if not session:
                return {
                    "success": False,
                    "message": "Escort session not found",
                    "citizen_id": citizen_id,
                }

            session.is_active = False
            return {
                "success": True,
                "citizen_id": citizen_id,
                "pin_verified": pin_verified,
                "message": "Escort session terminated nominal.",
            }

    def get_active_escorts(self) -> list[EscortSession]:
        """Return list of all currently active escort sessions."""
        with self._lock:
            return [s for s in self._sessions.values() if s.is_active]

    def check_timeouts(self) -> list[str]:
        """Identify escorts where heartbeat missed timeout or dead-man countdown expired."""
        with self._lock:
            now = datetime.now(timezone.utc)
            expired_citizens: list[str] = []

            for cid, session in self._sessions.items():
                if not session.is_active:
                    continue

                gap_seconds = (now - session.last_heartbeat).total_seconds()

                # Case 1: Active countdown hit zero
                if session.jerk_detected and session.countdown_remaining_sec <= 0:
                    session.alarm_triggered = True
                    expired_citizens.append(cid)
                # Case 2: Escort heartbeat completely stopped past timeout window
                elif gap_seconds > ESCORT_TIMEOUT_SEC:
                    session.jerk_detected = True
                    session.countdown_remaining_sec = 0
                    session.alarm_triggered = True
                    expired_citizens.append(cid)

            return expired_citizens


# Default module-level escort manager instance
_GLOBAL_ESCORT_MANAGER = EscortManager()


def get_default_escort_manager() -> EscortManager:
    """Return singleton instance of EscortManager."""
    return _GLOBAL_ESCORT_MANAGER


def process_telemetry(packet: dict[str, Any]) -> dict[str, Any]:
    """Process a full telemetry packet: check jerk, update position, compute heading change rate, return enriched packet with alerts.

    Expected packet keys:
    - citizen_id (str)
    - lat (float), lon (float)
    - accel_g (float) OR (accel_x, accel_y, accel_z)
    - speed_kmh (float, optional)
    - heading_deg (float, optional)
    - prev_heading_deg (float, optional)
    - time_delta_sec (float, optional)
    """
    citizen_id = str(packet.get("citizen_id", "CITIZEN_ANON"))
    lat = float(packet.get("lat", 26.8467))
    lon = float(packet.get("lon", 80.9462))
    speed_kmh = float(packet.get("speed_kmh", 0.0))
    heading_deg = float(packet.get("heading_deg", 0.0))

    # Compute acceleration magnitude if components given
    if "accel_g" in packet:
        accel_g = float(packet["accel_g"])
    elif "accel_x" in packet and "accel_y" in packet and "accel_z" in packet:
        ax = float(packet["accel_x"])
        ay = float(packet["accel_y"])
        az = float(packet["accel_z"])
        accel_g = math.sqrt(ax * ax + ay * ay + az * az)
    else:
        accel_g = 1.0  # Nominal Earth gravity 1.0g

    # Compute heading change rate
    time_delta_sec = float(packet.get("time_delta_sec", 1.0))
    prev_heading = packet.get("prev_heading_deg")

    if prev_heading is not None:
        diff_deg = abs((heading_deg - float(prev_heading) + 180.0) % 360.0 - 180.0)
        heading_change_rate_deg_s = diff_deg / max(time_delta_sec, 0.1)
    else:
        heading_change_rate_deg_s = 0.0

    # Jerk detection
    is_jerk = check_jerk_event(accel_g, threshold=JERK_THRESHOLD_G)

    # Update escort state via manager
    manager = get_default_escort_manager()
    heartbeat_state = manager.heartbeat(
        citizen_id=citizen_id,
        lat=lat,
        lon=lon,
        accel_g=accel_g,
        speed_kmh=speed_kmh,
        heading_deg=heading_deg,
    )

    # Check 3D optical surveillance status around current position
    surveillance_info = check_surveillance_status(lat, lon)

    # Assess overall alert level
    if heartbeat_state["should_trigger_alarm"]:
        alert_level = "CRITICAL_ALARM"
    elif is_jerk or heartbeat_state["jerk_detected"]:
        alert_level = "WARNING_JERK"
    elif heading_change_rate_deg_s > 45.0 and speed_kmh > 20.0:
        alert_level = "SUDDEN_DIVERSION"
    else:
        alert_level = "NOMINAL"

    timestamp_str = packet.get(
        "timestamp", datetime.now(timezone.utc).isoformat()
    )
    if isinstance(timestamp_str, datetime):
        timestamp_str = timestamp_str.isoformat()

    return {
        "citizen_id": citizen_id,
        "timestamp": timestamp_str,
        "position": {"lat": lat, "lon": lon},
        "telemetry": {
            "accel_g": round(accel_g, 3),
            "speed_kmh": round(speed_kmh, 1),
            "heading_deg": round(heading_deg, 1),
            "heading_change_rate_deg_s": round(heading_change_rate_deg_s, 2),
        },
        "alerts": {
            "jerk_detected": is_jerk,
            "sudden_diversion": (heading_change_rate_deg_s > 45.0 and speed_kmh > 20.0),
            "dead_man_countdown_active": heartbeat_state["jerk_detected"],
            "countdown_remaining_sec": heartbeat_state["countdown_remaining_sec"],
            "should_trigger_alarm": heartbeat_state["should_trigger_alarm"],
            "alert_level": alert_level,
        },
        "surveillance": {
            "status": surveillance_info["status"],
            "covering_cameras": surveillance_info["covering_cameras"],
            "recommendation": surveillance_info["recommendation"],
        },
        "status": "PROCESSED",
    }
