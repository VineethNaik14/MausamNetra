import json

from app.services.websocket_service import connection_manager

from tests.conftest import auth_headers


def test_websocket_connects_and_stays_open(client):
    with client.websocket_connect("/ws/incidents") as ws:
        assert ws is not None


def test_websocket_receives_broadcast_new_incident(client, user_token, source):
    with client.websocket_connect("/ws/incidents") as ws:
        # Submitting a report that the mock classifier tags as FLOOD should
        # create a new incident and broadcast NEW_INCIDENT to connected
        # clients (see ReportService._run_pipeline).
        resp = client.post(
            "/api/v1/reports",
            json={
                "source_id": str(source.id),
                "text": "Heavy rainfall has flooded roads across the district",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "city": "Bengaluru",
                "state": "Karnataka",
            },
            headers=auth_headers(user_token),
        )
        assert resp.status_code == 200

        raw = ws.receive_text()
        message = json.loads(raw)
        assert message["type"] == "NEW_INCIDENT"
        assert message["incident"]["event"] == "FLOOD"


def test_websocket_disconnect_removes_connection():
    initial_count = len(connection_manager._active_connections)
    from starlette.testclient import TestClient
    from app.main import app

    with TestClient(app).websocket_connect("/ws/incidents"):
        assert len(connection_manager._active_connections) == initial_count + 1

    # Connection manager should clean up once the client disconnects.
    assert len(connection_manager._active_connections) == initial_count
