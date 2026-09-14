from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.services.websocket_service import connection_manager

router = APIRouter(tags=["WebSocket"])
logger = get_logger(__name__)


@router.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    """
    Real-time incident feed.

    Broadcasts events of the shape:
        {"type": "NEW_INCIDENT", "incident": {...}}
        {"type": "INCIDENT_UPDATED", "incident": {...}}
        {"type": "REPORT_VERIFIED", "report_id": "...", "incident_id": "..."}
        {"type": "REPORT_REJECTED", "report_id": "..."}

    This endpoint currently just keeps the connection alive and listens for
    (and ignores) client pings; all data flows server -> client.
    """
    await connection_manager.connect(websocket)
    try:
        while True:
            # We don't require the client to send anything, but reading here
            # lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception:
        logger.exception("Unexpected WebSocket error")
        connection_manager.disconnect(websocket)
