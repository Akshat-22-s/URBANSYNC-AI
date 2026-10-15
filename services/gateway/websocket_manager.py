"""
UrbanSync AI - Centralized WebSocket Manager.
Handles channel groups: cockpit, citizen, field_worker.
Thread-safe connection tracking with robust JSON serialization.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Set
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger("gateway.websocket")


def default_json_serializer(obj: Any) -> Any:
    """Custom JSON serializer supporting datetimes, enums, UUIDs, and Pydantic models."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def serialize_payload(data: Any) -> str:
    """Serialize any python data structure or Pydantic model to a valid JSON string."""
    if isinstance(data, str):
        # Validate or pass through
        return data
    if isinstance(data, BaseModel):
        return data.model_dump_json()
    return json.dumps(data, default=default_json_serializer)


class WebSocketManager:
    """
    Centralized manager maintaining active WebSocket connections partitioned into:
    - cockpit: City Command Center & dispatch consoles
    - citizen: Mobile companion app users
    - field_worker: Sanitation trucks, first responders, and field patrols
    """

    VALID_CHANNELS = {"cockpit", "citizen", "field_worker"}

    def __init__(self) -> None:
        self._channels: Dict[str, Set[WebSocket]] = {
            "cockpit": set(),
            "citizen": set(),
            "field_worker": set(),
        }
        self._lock = asyncio.Lock()

    def _normalize_channel(self, channel: str) -> str:
        """Normalize channel names like 'field-worker' to 'field_worker'."""
        normalized = channel.strip().lower().replace("-", "_")
        if normalized not in self.VALID_CHANNELS:
            logger.warning(f"Unknown channel '{channel}' - defaulting to 'cockpit'")
            return "cockpit"
        return normalized

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept WebSocket connection and register it in the designated channel group."""
        await websocket.accept()
        norm_channel = self._normalize_channel(channel)
        async with self._lock:
            self._channels[norm_channel].add(websocket)
            total = sum(len(conns) for conns in self._channels.values())
            logger.info(
                f"WebSocket connected to channel '{norm_channel}'. "
                f"Active in '{norm_channel}': {len(self._channels[norm_channel])}, Total: {total}"
            )

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Deregister WebSocket connection from the designated channel group."""
        norm_channel = self._normalize_channel(channel)
        async with self._lock:
            if websocket in self._channels[norm_channel]:
                self._channels[norm_channel].remove(websocket)
                logger.info(
                    f"WebSocket disconnected from channel '{norm_channel}'. "
                    f"Remaining in '{norm_channel}': {len(self._channels[norm_channel])}"
                )

    async def broadcast(self, channel: str, data: Any) -> int:
        """
        Broadcast message to all active WebSockets in a given channel group.
        Stale/broken sockets are removed automatically.
        Returns the count of successfully sent messages.
        """
        norm_channel = self._normalize_channel(channel)
        payload = serialize_payload(data)

        async with self._lock:
            sockets = list(self._channels[norm_channel])

        if not sockets:
            return 0

        stale_sockets: Set[WebSocket] = set()
        successful = 0

        for ws in sockets:
            try:
                await ws.send_text(payload)
                successful += 1
            except Exception as exc:
                logger.debug(f"Failed to send to client in '{norm_channel}': {exc}")
                stale_sockets.add(ws)

        if stale_sockets:
            async with self._lock:
                for stale in stale_sockets:
                    self._channels[norm_channel].discard(stale)

        return successful

    async def broadcast_all(self, data: Any) -> int:
        """Broadcast message to all connected clients across all channels."""
        payload = serialize_payload(data)
        total_success = 0
        for channel in self.VALID_CHANNELS:
            total_success += await self.broadcast(channel, payload)
        return total_success

    def get_stats(self) -> Dict[str, int]:
        """Return snapshot of active connection counts per channel."""
        return {
            "cockpit": len(self._channels["cockpit"]),
            "citizen": len(self._channels["citizen"]),
            "field_worker": len(self._channels["field_worker"]),
            "total": sum(len(c) for c in self._channels.values()),
        }


# Global singleton manager instance
ws_manager = WebSocketManager()
