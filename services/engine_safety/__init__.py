"""UrbanSync AI Safety Engine.

Provides intelligent routing, dual-PIN duress verification, volumetric
CCTV occlusion raycasting, and siren telemetry/jerk detection for women's
and citizens' urban safety.
"""

from .safepath_router import compute_safepath
from .duress_auth import verify_pin, DuressResult
from .occlusion_raycast import check_surveillance_status
from .siren_telemetry import process_telemetry, check_jerk_event

__all__ = [
    "compute_safepath",
    "verify_pin",
    "DuressResult",
    "check_surveillance_status",
    "process_telemetry",
    "check_jerk_event",
]
