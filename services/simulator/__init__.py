"""
UrbanSync AI - Simulation Daemon and Mock Streams Package
=========================================================
"""

from .mock_streams import (
    generate_citizen_packet,
    generate_dispatch_event,
    generate_green_corridor,
    generate_snatch_event,
    generate_waste_update,
    get_initial_bins,
    get_initial_citizens,
)
from .telemetry_daemon import (
    TelemetryPublisher,
    main,
)

__all__ = [
    "generate_citizen_packet",
    "generate_dispatch_event",
    "generate_green_corridor",
    "generate_snatch_event",
    "generate_waste_update",
    "get_initial_bins",
    "get_initial_citizens",
    "TelemetryPublisher",
    "main",
]
