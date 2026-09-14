from tests.conftest import auth_headers


def _create_flood_report(client, token, source, **overrides):
    payload = {
        "source_id": str(source.id),
        "text": "Heavy rainfall has flooded roads near the city center",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
    }
    payload.update(overrides)
    return client.post("/api/v1/reports", json=payload, headers=auth_headers(token))


def test_events_requires_auth(client):
    resp = client.get("/api/v1/events")
    assert resp.status_code == 401


def test_creating_report_creates_incident_and_is_listed(client, user_token, source):
    create_resp = _create_flood_report(client, user_token, source)
    assert create_resp.status_code == 200
    incident_id = create_resp.json()["data"]["incident_id"]
    assert incident_id is not None

    resp = client.get("/api/v1/events", headers=auth_headers(user_token))
    assert resp.status_code == 200
    ids = [i["id"] for i in resp.json()["data"]]
    assert incident_id in ids


def test_get_event_by_id(client, user_token, source):
    create_resp = _create_flood_report(client, user_token, source)
    incident_id = create_resp.json()["data"]["incident_id"]

    resp = client.get(f"/api/v1/events/{incident_id}", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == incident_id
    assert resp.json()["data"]["event_type"] == "FLOOD"


def test_get_event_not_found(client, user_token):
    import uuid

    resp = client.get(f"/api/v1/events/{uuid.uuid4()}", headers=auth_headers(user_token))
    assert resp.status_code == 404


def test_map_endpoint_returns_lightweight_points(client, user_token, source):
    _create_flood_report(client, user_token, source)

    resp = client.get("/api/v1/events/map", headers=auth_headers(user_token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    point = data[0]
    # Map payload should be minimal - just enough for a Leaflet marker.
    assert set(point.keys()) == {"id", "event_type", "severity", "status", "latitude", "longitude", "report_count"}
