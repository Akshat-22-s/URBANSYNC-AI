"""
UrbanSync AI - Telemetry Simulation Daemon
==========================================
Asynchronous simulation daemon driving continuous urban city telemetry:
1. GPS Kinematics: 50 simulated citizens undergoing random walk (lat/lon jitter, heading, speed).
   Published to Redis 'city:telemetry:kinematics' every 2 seconds.
2. Waste Accumulation: 30 smart municipal bins with Poisson fill increases.
   Published to Redis 'city:waste:deltas' every 10 seconds.
3. Snatch Anomaly Events: Poisson process (lambda=0.02 per tick) generating jerk events with accel_g > 3.0.
   Published to Redis 'city:safety:alerts'.
4. Emergency Patrol Dispatches: Intermittent emergency responder updates.
   Published to Redis 'city:telemetry:kinematics'.
5. Green Corridor Updates: Active green wave traffic light phase synchronizations.
   Published to Redis 'city:mobility:green_corridors' every 30 seconds.

Features graceful shutdown, signal handling, and connection resilience.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import redis.asyncio as aioredis

from services.simulator.mock_streams import (
    generate_citizen_packet,
    generate_dispatch_event,
    generate_green_corridor,
    generate_snatch_event,
    generate_waste_update,
    get_initial_bins,
    get_initial_citizens,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [TelemetryDaemon] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TelemetryDaemon")

# Configuration constants
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CHANNEL_KINEMATICS = "city:telemetry:kinematics"
CHANNEL_WASTE = "city:waste:deltas"
CHANNEL_SAFETY_ALERTS = "city:safety:alerts"
CHANNEL_GREEN_CORRIDORS = "city:mobility:green_corridors"

KINEMATICS_INTERVAL_SEC = 2.0
WASTE_INTERVAL_SEC = 10.0
GREEN_CORRIDOR_INTERVAL_SEC = 30.0
DISPATCH_INTERVAL_SEC = 12.0
SNATCH_LAMBDA = 0.02


class TelemetryPublisher:
    """
    Manages asynchronous Redis connection and safe message publishing with fallback logging.
    """

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish Redis asynchronous connection with retry tolerance."""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("Connected successfully to Redis pub/sub at %s", self.redis_url)
        except Exception as exc:
            self._connected = False
            logger.warning(
                "Redis connection failed (%s). Simulation daemon running with local message logging fallback.",
                exc
            )

    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """
        Publish a JSON-encoded message to a Redis channel.

        Parameters
        ----------
        channel : str
            Target Redis pub/sub channel.
        message : dict
            Message payload dictionary.
        """
        serialized = json.dumps(message)
        if self._connected and self.redis_client:
            try:
                await self.redis_client.publish(channel, serialized)
                return
            except Exception as exc:
                self._connected = False
                logger.warning("Error publishing to channel %s: %s. Switching to fallback.", channel, exc)

        # Fallback logging when Redis is unavailable
        logger.debug("[FALLBACK PUB] Channel: %s | Payload: %s", channel, serialized[:120])

    async def close(self) -> None:
        """Close connection cleanly."""
        if self.redis_client:
            try:
                await self.redis_client.aclose()
                logger.info("Redis connection closed cleanly.")
            except Exception as exc:
                logger.debug("Error while closing Redis: %s", exc)


async def citizen_kinematics_worker(
    publisher: TelemetryPublisher,
    citizens: List[Dict[str, Any]],
    shutdown_event: asyncio.Event
) -> None:
    """
    Worker task updating 50 citizens' random walk kinematics every 2 seconds
    and randomly generating snatch anomaly events according to Poisson(lambda=0.02).
    """
    logger.info("Citizen kinematics worker started (Tracking %d citizens, interval=%.1fs)", len(citizens), KINEMATICS_INTERVAL_SEC)

    while not shutdown_event.is_set():
        try:
            # 1. Update GPS kinematics for all citizens
            for citizen in citizens:
                packet = generate_citizen_packet(
                    citizen_id=citizen["citizen_id"],
                    base_lat=citizen["lat"],
                    base_lon=citizen["lon"]
                )
                # Persist updated location for subsequent random walk step
                citizen["lat"] = packet["lat"]
                citizen["lon"] = packet["lon"]
                citizen["heading"] = packet["heading"]
                citizen["speed_mps"] = packet["speed_mps"]

                await publisher.publish(CHANNEL_KINEMATICS, packet)

            # 2. Check for random snatch events (Poisson process lambda=0.02 per tick)
            snatch_occurrences = int(np.random.poisson(lam=SNATCH_LAMBDA))
            if snatch_occurrences > 0:
                for _ in range(snatch_occurrences):
                    target_citizen = citizens[int(np.random.randint(0, len(citizens)))]
                    alert_packet = generate_snatch_event(
                        citizen_id=target_citizen["citizen_id"],
                        lat=target_citizen["lat"],
                        lon=target_citizen["lon"]
                    )
                    logger.warning(
                        "[CRITICAL SAFETY ALERT] Snatch detected for citizen %s (accel=%.2f g, jerk=%.2f g/s) at (%f, %f)",
                        alert_packet["citizen_id"],
                        alert_packet["accel_g"],
                        alert_packet["jerk_g_per_sec"],
                        alert_packet["lat"],
                        alert_packet["lon"]
                    )
                    await publisher.publish(CHANNEL_SAFETY_ALERTS, alert_packet)

            # Wait for next tick or shutdown
            await asyncio.wait_for(shutdown_event.wait(), timeout=KINEMATICS_INTERVAL_SEC)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in citizen kinematics loop: %s", exc)
            await asyncio.sleep(1.0)


async def waste_accumulation_worker(
    publisher: TelemetryPublisher,
    bins: List[Dict[str, Any]],
    shutdown_event: asyncio.Event
) -> None:
    """
    Worker task generating Poisson-distributed fill rate increments for 30 waste bins every 10 seconds.
    """
    logger.info("Waste accumulation worker started (Monitoring %d bins, interval=%.1fs)", len(bins), WASTE_INTERVAL_SEC)

    while not shutdown_event.is_set():
        try:
            for b in bins:
                update_packet = generate_waste_update(
                    bin_id=b["bin_id"],
                    current_fill=b["current_fill_pct"]
                )
                b["current_fill_pct"] = update_packet["current_fill_pct"]

                # If bin exceeded 95%, simulate rapid municipal empty cycle on next turn
                if b["current_fill_pct"] >= 95.0:
                    b["current_fill_pct"] = round(float(np.random.uniform(10.0, 20.0)), 1)

                await publisher.publish(CHANNEL_WASTE, update_packet)

            await asyncio.wait_for(shutdown_event.wait(), timeout=WASTE_INTERVAL_SEC)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in waste accumulation loop: %s", exc)
            await asyncio.sleep(2.0)


async def patrol_dispatch_worker(
    publisher: TelemetryPublisher,
    shutdown_event: asyncio.Event
) -> None:
    """
    Worker task generating periodic emergency vehicle movements and dispatch alerts.
    """
    logger.info("Emergency patrol dispatch worker started (interval=%.1fs)", DISPATCH_INTERVAL_SEC)

    while not shutdown_event.is_set():
        try:
            dispatch_packet = generate_dispatch_event()
            await publisher.publish(CHANNEL_KINEMATICS, dispatch_packet)
            logger.info(
                "Dispatched %s (%s) -> ETA: %.1f min",
                dispatch_packet["unit_id"],
                dispatch_packet["unit_type"],
                dispatch_packet["eta_min"]
            )
            await asyncio.wait_for(shutdown_event.wait(), timeout=DISPATCH_INTERVAL_SEC)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in patrol dispatch loop: %s", exc)
            await asyncio.sleep(3.0)


async def green_corridor_worker(
    publisher: TelemetryPublisher,
    shutdown_event: asyncio.Event
) -> None:
    """
    Worker task broadcasting green wave corridor synchronizations every 30 seconds.
    """
    logger.info("Green corridor synchronization worker started (interval=%.1fs)", GREEN_CORRIDOR_INTERVAL_SEC)

    while not shutdown_event.is_set():
        try:
            corridor_packet = generate_green_corridor()
            await publisher.publish(CHANNEL_GREEN_CORRIDORS, corridor_packet)
            logger.info(
                "Green corridor broadcast: %s (%d intersections synchronized)",
                corridor_packet["corridor_id"],
                len(corridor_packet.get("intersections", []))
            )
            await asyncio.wait_for(shutdown_event.wait(), timeout=GREEN_CORRIDOR_INTERVAL_SEC)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Error in green corridor loop: %s", exc)
            await asyncio.sleep(5.0)


def setup_signal_handlers(shutdown_event: asyncio.Event) -> None:
    """
    Configure cross-platform signal handlers for SIGINT and SIGTERM.
    """
    def _trigger_shutdown(sig_name: str) -> None:
        logger.info("Received termination signal (%s). Initiating graceful shutdown...", sig_name)
        shutdown_event.set()

    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig.name: _trigger_shutdown(s))
        except (NotImplementedError, AttributeError):
            # Fallback for Windows Proactor event loop
            try:
                signal.signal(sig, lambda s, f, name=sig.name: _trigger_shutdown(name))
            except Exception as e:
                logger.debug("Could not attach fallback signal %s: %e", sig, e)


async def main() -> None:
    """
    Main asynchronous entry point executing all simulation loops concurrently.
    """
    logger.info("Starting UrbanSync AI Telemetry Daemon...")
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    publisher = TelemetryPublisher(redis_url=REDIS_URL)
    await publisher.connect()

    # Initialize simulation entities
    citizens = get_initial_citizens(n=50)
    bins = get_initial_bins(n=30)
    logger.info("Initialized %d citizens and %d smart bins.", len(citizens), len(bins))

    # Launch background worker tasks
    tasks = [
        asyncio.create_task(citizen_kinematics_worker(publisher, citizens, shutdown_event)),
        asyncio.create_task(waste_accumulation_worker(publisher, bins, shutdown_event)),
        asyncio.create_task(patrol_dispatch_worker(publisher, shutdown_event)),
        asyncio.create_task(green_corridor_worker(publisher, shutdown_event)),
    ]

    try:
        # Await shutdown signal
        await shutdown_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Daemon interrupted.")
    finally:
        logger.info("Cancelling active simulation tasks...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await publisher.close()
        logger.info("UrbanSync AI Telemetry Daemon stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
