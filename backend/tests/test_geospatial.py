from tests.conftest import auth_headers


def _create_flood_report(client, token, source, lat, lon, **overrides):
    payload = {
        "source_id": str(source.id),
        "text": "Heavy rainfall has flooded roads in the area",
        "latitude": lat,
        "longitude": lon,
        "city": overrides.pop("city", "Bengaluru"),
        "state": overrides.pop("state", "Karnataka"),
    }
    payload.update(overrides)
    return client.post("/api/v1/reports", json=payload, headers=auth_headers(token))


def test_nearby_finds_incident_within_radius(client, user_token, source):
    # Bengaluru city center (MG Road area)
    _create_flood_report(client, user_token, source, 12.9716, 77.5946)

    resp = client.get(
        "/api/v1/events/nearby",
        params={"latitude": 12.9750, "longitude": 77.6000, "radius_km": 10},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert "distance_km" in data[0]
    assert data[0]["distance_km"] < 10


def test_nearby_excludes_incidents_outside_radius(client, user_token, source):
    # Create an incident far away (Mumbai, ~840km from Bengaluru)
    _create_flood_report(client, user_token, source, 19.0760, 72.8777, city="Mumbai", state="Maharashtra")

    resp = client.get(
        "/api/v1/events/nearby",
        params={"latitude": 12.9716, "longitude": 77.5946, "radius_km": 10},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_nearby_respects_event_filter(client, user_token, source):
    _create_flood_report(client, user_token, source, 12.9716, 77.5946)

    resp = client.get(
        "/api/v1/events/nearby",
        params={"latitude": 12.9716, "longitude": 77.5946, "radius_km": 10, "event": "heatwave"},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_nearby_requires_valid_coordinates(client, user_token):
    resp = client.get(
        "/api/v1/events/nearby",
        params={"latitude": 999, "longitude": 77.6, "radius_km": 10},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 422
