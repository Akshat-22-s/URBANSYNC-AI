"""
UrbanSync AI - Central API Gateway Service.
Main entry point orchestrating Mobility, Safety, Sanitation, and Dispatch modules.
Provides REST APIs, real-time WebSocket channels, and Redis PubSub telemetry streaming.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gateway.main")

# Support both package-relative and direct imports
try:
    from .websocket_manager import ws_manager
    from .routers import dispatch, mobility, sanitation, safety
except ImportError:
    from websocket_manager import ws_manager
    from routers import dispatch, mobility, sanitation, safety


# ============================================================================
# Redis Background Telemetry Subscriber
# ============================================================================

REDIS_CHANNELS = [
    "city:telemetry:kinematics",
    "city:waste:deltas",
    "city:mobility:green_corridors",
    "city:safety:alerts",
]


async def run_redis_subscriber(redis_url: str) -> None:
    """
    Subscribes to city telemetry message channels on Redis Pub/Sub
    and propagates payloads to targeted WebSocket channels:
    - city:telemetry:kinematics -> cockpit, citizen
    - city:waste:deltas -> cockpit, field_worker
    - city:mobility:green_corridors -> cockpit, field_worker
    - city:safety:alerts -> cockpit, citizen, field_worker (all)
    """
    try:
        import redis.asyncio as aioredis
    except ImportError:
        logger.warning("Redis client library not available. Telemetry subscriber aborted.")
        return

    while True:
        client = None
        pubsub = None
        try:
            logger.info(f"Connecting subscriber to Redis at {redis_url}...")
            client = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(*REDIS_CHANNELS)
            logger.info(f"Subscribed to Redis channels: {REDIS_CHANNELS}")

            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    ch = message.get("channel")
                    data = message.get("data")

                    if ch == "city:telemetry:kinematics":
                        await ws_manager.broadcast("cockpit", data)
                        await ws_manager.broadcast("citizen", data)
                    elif ch == "city:waste:deltas":
                        await ws_manager.broadcast("cockpit", data)
                        await ws_manager.broadcast("field_worker", data)
                    elif ch == "city:mobility:green_corridors":
                        await ws_manager.broadcast("cockpit", data)
                        await ws_manager.broadcast("field_worker", data)
                    elif ch == "city:safety:alerts":
                        await ws_manager.broadcast_all(data)

        except asyncio.CancelledError:
            logger.info("Redis subscriber task cancelled.")
            break
        except Exception as exc:
            logger.warning(f"Redis subscriber connection error: {exc}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            if pubsub:
                try:
                    await pubsub.close()
                except Exception:
                    pass
            if client:
                try:
                    await client.aclose()
                except Exception:
                    pass


# ============================================================================
# Application Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager:
    1. Initializes Redis connection pool and validates connectivity.
    2. Spawns background Redis Pub/Sub subscriber task.
    3. Handles clean resource teardown on shutdown.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app.state.redis = None
    subscriber_task: Optional[asyncio.Task] = None

    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(redis_url, decode_responses=True)
        # Attempt connection check with short timeout
        await asyncio.wait_for(client.ping(), timeout=2.5)
        app.state.redis = client
        logger.info(f"Successfully connected to Redis instance at {redis_url}")
        subscriber_task = asyncio.create_task(run_redis_subscriber(redis_url))
    except Exception as exc:
        logger.warning(
            f"Unable to connect to Redis at {redis_url} ({exc}). Running gateway in in-memory mode."
        )

    yield

    # Teardown
    if subscriber_task:
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass

    if app.state.redis:
        try:
            await app.state.redis.aclose()
            logger.info("Redis connection closed cleanly.")
        except Exception as exc:
            logger.debug(f"Error during Redis shutdown: {exc}")


# ============================================================================
# FastAPI Application Declaration
# ============================================================================

app = FastAPI(
    title="UrbanSync AI - Central API Gateway",
    description=(
        "Unified intelligent urban operations gateway coordinating Mobility (SILN & green waves), "
        "Public Safety (SafePath dual routing & citizen escort monitoring), Sanitation (CVRP & vision), "
        "and Real-time Emergency Dispatch orchestration."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
origins = (
    [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
    if allowed_origins_raw != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(dispatch.router)
app.include_router(mobility.router)
app.include_router(sanitation.router)
app.include_router(safety.router)


# ============================================================================
# Core Informational & Health Endpoints
# ============================================================================

@app.get("/", summary="Gateway API Index")
async def root() -> dict:
    """Returns gateway service information, active modules, and endpoint directories."""
    return {
        "service": "UrbanSync AI Central API Gateway",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "documentation": "/docs",
        "subsystems": {
            "dispatch": "/api/dispatch",
            "mobility": "/api/mobility",
            "sanitation": "/api/sanitation",
            "safety": "/api/safety",
        },
        "websockets": [
            "/ws/cockpit",
            "/ws/citizen",
            "/ws/field-worker",
        ],
    }


@app.get("/health", summary="Health Check")
async def health_check() -> dict:
    """
    Monitors gateway operational health, Redis connection state,
    and active WebSocket client connectivity metrics.
    """
    redis_active = False
    redis_client = getattr(app.state, "redis", None)
    if redis_client:
        try:
            await redis_client.ping()
            redis_active = True
        except Exception:
            redis_active = False

    return {
        "status": "healthy",
        "service": "urbansync-gateway",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis_connected": redis_active,
        "active_ws_connections": ws_manager.get_stats(),
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/cockpit")
async def ws_cockpit_endpoint(websocket: WebSocket) -> None:
    """
    Command Center Cockpit WebSocket stream.
    Receives real-time telemetry, emergency alerts, reroute events, and fleet coordinates.
    """
    await ws_manager.connect(websocket, "cockpit")
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "cockpit")
    except Exception as exc:
        logger.debug(f"Cockpit WS connection exception: {exc}")
        await ws_manager.disconnect(websocket, "cockpit")


@app.websocket("/ws/citizen")
async def ws_citizen_endpoint(websocket: WebSocket) -> None:
    """
    Citizen Mobile Companion WebSocket stream.
    Receives safety alerts, active escort updates, and proximity hazard advisories.
    """
    await ws_manager.connect(websocket, "citizen")
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "citizen")
    except Exception as exc:
        logger.debug(f"Citizen WS connection exception: {exc}")
        await ws_manager.disconnect(websocket, "citizen")


@app.websocket("/ws/field-worker")
@app.websocket("/ws/field_worker")
async def ws_field_worker_endpoint(websocket: WebSocket) -> None:
    """
    Field Worker & Sanitation Fleet WebSocket stream.
    Receives waste bin overflow alerts, dynamically optimized collection schedules,
    and first-responder dispatch alerts.
    """
    await ws_manager.connect(websocket, "field_worker")
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "field_worker")
    except Exception as exc:
        logger.debug(f"Field Worker WS connection exception: {exc}")
        await ws_manager.disconnect(websocket, "field_worker")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8000, reload=True)
