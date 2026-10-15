"""Dual-PIN duress verification system.

PIN 1234: Safe verification — nominal trip end, reset alarm.
PIN 9999: Duress trigger — display deceptive 'Trip Ended Safely' while
          silently dispatching CODE_RED_P1 to UP-112 CAD.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

DEFAULT_SAFE_PIN = "1234"
DEFAULT_DURESS_PIN = "9999"
MAX_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(minutes=5)
UP112_CAD_ENDPOINT = "https://cad.up112.police.gov.in/api/v1/dispatch"


@dataclass
class DuressResult:
    """Outcome of a citizen PIN verification request."""

    pin_type: str  # "SAFE", "DURESS", "INVALID", "LOCKED"
    display_message: str
    silent_dispatch: bool
    escalation_code: str | None
    citizen_id: str
    timestamp: datetime
    coordinates: tuple[float, float] | None = None
    attempts_remaining: int = MAX_ATTEMPTS
    is_locked: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert dataclass to serializable dictionary."""
        return {
            "pin_type": self.pin_type,
            "display_message": self.display_message,
            "silent_dispatch": self.silent_dispatch,
            "escalation_code": self.escalation_code,
            "citizen_id": self.citizen_id,
            "timestamp": self.timestamp.isoformat(),
            "coordinates": self.coordinates,
            "attempts_remaining": self.attempts_remaining,
            "is_locked": self.is_locked,
        }


class PinAttemptTracker:
    """Thread-safe tracker for failed PIN verification attempts and lockout enforcement."""

    def __init__(self, max_attempts: int = MAX_ATTEMPTS, lockout_duration: timedelta = LOCKOUT_DURATION) -> None:
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self._lock = threading.Lock()
        self._attempts: dict[str, int] = {}
        self._lockout_until: dict[str, datetime] = {}

    def is_locked(self, citizen_id: str) -> bool:
        """Check if a citizen is currently locked out."""
        with self._lock:
            lockout_time = self._lockout_until.get(citizen_id)
            if not lockout_time:
                return False

            now = datetime.now(timezone.utc)
            if now < lockout_time:
                return True

            # Lockout expired, clear lockout and attempts
            del self._lockout_until[citizen_id]
            self._attempts.pop(citizen_id, None)
            return False

    def record_attempt(self, citizen_id: str, success: bool) -> None:
        """Record a verification attempt (success resets attempts, failure increments count)."""
        with self._lock:
            now = datetime.now(timezone.utc)
            if success:
                self._attempts.pop(citizen_id, None)
                self._lockout_until.pop(citizen_id, None)
                return

            current_fails = self._attempts.get(citizen_id, 0) + 1
            self._attempts[citizen_id] = current_fails

            if current_fails >= self.max_attempts:
                self._lockout_until[citizen_id] = now + self.lockout_duration

    def get_remaining_attempts(self, citizen_id: str) -> int:
        """Get the number of remaining PIN attempts before lockout."""
        with self._lock:
            lockout_time = self._lockout_until.get(citizen_id)
            if lockout_time:
                if datetime.now(timezone.utc) < lockout_time:
                    return 0
                # Expired lockout
                del self._lockout_until[citizen_id]
                self._attempts.pop(citizen_id, None)
                return self.max_attempts

            fails = self._attempts.get(citizen_id, 0)
            return max(0, self.max_attempts - fails)

    def get_lockout_remaining_seconds(self, citizen_id: str) -> int:
        """Return remaining seconds in lockout, or 0 if not locked."""
        with self._lock:
            lockout_time = self._lockout_until.get(citizen_id)
            if not lockout_time:
                return 0
            now = datetime.now(timezone.utc)
            if now >= lockout_time:
                del self._lockout_until[citizen_id]
                self._attempts.pop(citizen_id, None)
                return 0
            return int((lockout_time - now).total_seconds())

    def reset(self, citizen_id: str) -> None:
        """Manually clear all attempt history and lockout state for a citizen."""
        with self._lock:
            self._attempts.pop(citizen_id, None)
            self._lockout_until.pop(citizen_id, None)


# Default module-level tracker instance
_GLOBAL_TRACKER = PinAttemptTracker()


def verify_pin(
    citizen_id: str,
    pin: str,
    lat: float | None = None,
    lon: float | None = None,
    safe_pin: str = DEFAULT_SAFE_PIN,
    duress_pin: str = DEFAULT_DURESS_PIN,
    tracker: PinAttemptTracker | None = None,
) -> DuressResult:
    """Verify the entered PIN against Safe and Duress pins.

    If pin == safe_pin:
        Safe verification — nominal trip end, reset alarm.
        Returns DuressResult(SAFE, 'Trip Ended Safely ✓', silent_dispatch=False, escalation_code='CODE_GREEN')

    If pin == duress_pin:
        Duress trigger — displays deceptive 'Trip Ended Safely ✓' while
        silently dispatching CODE_RED_P1 to UP-112 CAD.
        Returns DuressResult(DURESS, 'Trip Ended Safely ✓', silent_dispatch=True, escalation_code='CODE_RED_P1')

    Otherwise:
        Returns invalid PIN result with remaining attempts tracking and 5-min lockout after 3 fails.
    """
    if tracker is None:
        tracker = _GLOBAL_TRACKER

    now = datetime.now(timezone.utc)
    coords = (lat, lon) if (lat is not None and lon is not None) else None

    # Check if user is locked out
    if tracker.is_locked(citizen_id):
        remaining_secs = tracker.get_lockout_remaining_seconds(citizen_id)
        mins = max(1, (remaining_secs + 59) // 60)
        return DuressResult(
            pin_type="LOCKED",
            display_message=f"Account locked due to multiple failed attempts. Please retry in {mins} minute(s).",
            silent_dispatch=False,
            escalation_code="CODE_AMBER_LOCKOUT",
            citizen_id=citizen_id,
            timestamp=now,
            coordinates=coords,
            attempts_remaining=0,
            is_locked=True,
        )

    # Clean PIN string
    pin_str = str(pin).strip()

    # 1. Nominal Safe PIN verification
    if pin_str == str(safe_pin).strip():
        tracker.record_attempt(citizen_id, success=True)
        return DuressResult(
            pin_type="SAFE",
            display_message="Trip Ended Safely ✓",
            silent_dispatch=False,
            escalation_code="CODE_GREEN",
            citizen_id=citizen_id,
            timestamp=now,
            coordinates=coords,
            attempts_remaining=MAX_ATTEMPTS,
            is_locked=False,
        )

    # 2. Silent Duress PIN verification (identical deceptive UI message)
    if pin_str == str(duress_pin).strip():
        # Do not mark as failed attempt to avoid alerting aggressor
        tracker.record_attempt(citizen_id, success=True)
        return DuressResult(
            pin_type="DURESS",
            display_message="Trip Ended Safely ✓",
            silent_dispatch=True,
            escalation_code="CODE_RED_P1",
            citizen_id=citizen_id,
            timestamp=now,
            coordinates=coords,
            attempts_remaining=MAX_ATTEMPTS,
            is_locked=False,
        )

    # 3. Invalid PIN entered
    tracker.record_attempt(citizen_id, success=False)
    remaining = tracker.get_remaining_attempts(citizen_id)
    is_now_locked = tracker.is_locked(citizen_id)

    if is_now_locked:
        msg = "Too many failed attempts. Device verification locked for 5 minutes."
        code = "CODE_AMBER_LOCKOUT"
    else:
        msg = f"Invalid PIN. {remaining} attempt(s) remaining."
        code = None

    return DuressResult(
        pin_type="INVALID",
        display_message=msg,
        silent_dispatch=False,
        escalation_code=code,
        citizen_id=citizen_id,
        timestamp=now,
        coordinates=coords,
        attempts_remaining=remaining,
        is_locked=is_now_locked,
    )


def build_escalation_payload(result: DuressResult) -> dict[str, Any]:
    """Build the full escalation payload for UP-112 CAD dispatch.

    Payload format:
    {
        citizen_id,
        lat,
        lon,
        pin_type,
        timestamp,
        code,
        priority: 'P1_IMMEDIATE',
        cad_endpoint,
        responding_units: ['PATROL_1', 'PATROL_2']
    }
    """
    coords = result.coordinates or (None, None)
    priority = "P1_IMMEDIATE" if result.silent_dispatch else ("P3_STANDARD" if result.pin_type == "SAFE" else "P2_ELEVATED")

    payload: dict[str, Any] = {
        "citizen_id": result.citizen_id,
        "lat": coords[0],
        "lon": coords[1],
        "pin_type": result.pin_type,
        "timestamp": result.timestamp.isoformat(),
        "code": result.escalation_code or "CODE_AMBER",
        "priority": priority,
        "cad_endpoint": UP112_CAD_ENDPOINT,
        "responding_units": ["PATROL_1", "PATROL_2"],
        "tactical_meta": {
            "silent_duress": result.silent_dispatch,
            "victim_deception_active": result.silent_dispatch,
            "cad_jurisdiction": "UP_POLICE_COMMISSIONERATE_LUCKNOW",
            "dispatch_urgency": "IMMEDIATE_INTERVENTION" if result.silent_dispatch else "ROUTINE",
            "booth_network_sync": True,
        },
    }
    return payload
