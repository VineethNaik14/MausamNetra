"""
WebSocket manager for real-time incident/report events.

Keeps a simple in-memory set of connected clients. For a multi-instance
deployment this would need a shared pub/sub backend (e.g. Redis), but an
in-memory manager is sufficient and appropriate for this hackathon MVP.
"""
import json
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info("WebSocket connected. Active connections: %d", len(self._active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._active_connections.discard(websocket)
        logger.info("WebSocket disconnected. Active connections: %d", len(self._active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for connection in self._active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)


# Module-level singleton - simple and sufficient for a single-process prototype.
connection_manager = ConnectionManager()


class WebSocketService:
    """Thin wrapper exposing typed broadcast helpers for domain events."""

    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager

    async def broadcast_new_incident(self, incident: dict[str, Any]) -> None:
        await self.manager.broadcast({"type": "NEW_INCIDENT", "incident": incident})

    async def broadcast_incident_updated(self, incident: dict[str, Any]) -> None:
        await self.manager.broadcast({"type": "INCIDENT_UPDATED", "incident": incident})

    async def broadcast_report_verified(self, report_id: str, incident_id: str | None) -> None:
        await self.manager.broadcast(
            {"type": "REPORT_VERIFIED", "report_id": report_id, "incident_id": incident_id}
        )

    async def broadcast_report_rejected(self, report_id: str) -> None:
        await self.manager.broadcast({"type": "REPORT_REJECTED", "report_id": report_id})


def get_websocket_service() -> WebSocketService:
    return WebSocketService(connection_manager)
