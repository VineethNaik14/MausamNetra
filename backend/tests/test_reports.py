from tests.conftest import auth_headers


def _report_payload(source_id, **overrides):
    payload = {
        "source_id": str(source_id),
        "text": "Heavy rainfall has flooded roads near MG Road",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
    }
    payload.update(overrides)
    return payload


def test_create_report_requires_auth(client, source):
    resp = client.post("/api/v1/reports", json=_report_payload(source.id))
    assert resp.status_code == 401


def test_create_report_success(client, user_token, source):
    resp = client.post(
        "/api/v1/reports", json=_report_payload(source.id), headers=auth_headers(user_token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["latitude"] == 12.9716
    assert data["longitude"] == 77.5946
    # The mock classifier should detect "flooded" -> FLOOD
    assert data["event_type"] == "FLOOD"
    assert data["status"] == "PROCESSED"


def test_create_report_invalid_source(client, user_token):
    import uuid

    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(uuid.uuid4()),
        headers=auth_headers(user_token),
    )
    # A nonexistent source_id is a semantic validation failure (see
    # app.core.exceptions.ValidationError), not a 404 - the request body
    # itself was well-formed, but references invalid related data.
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_report_inactive_source(client, user_token, inactive_source):
    resp = client.post(
        "/api/v1/reports", json=_report_payload(inactive_source.id), headers=auth_headers(user_token)
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_report_invalid_latitude(client, user_token, source):
    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(source.id, latitude=120.0),
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 422


def test_create_report_invalid_longitude(client, user_token, source):
    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(source.id, longitude=-200.0),
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 422


def test_create_report_blank_text(client, user_token, source):
    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(source.id, text="   "),
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 422


def test_get_report_by_id(client, user_token, source):
    create_resp = client.post(
        "/api/v1/reports", json=_report_payload(source.id), headers=auth_headers(user_token)
    )
    report_id = create_resp.json()["data"]["id"]

    resp = client.get(f"/api/v1/reports/{report_id}", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == report_id


def test_get_report_not_found(client, user_token):
    import uuid

    resp = client.get(f"/api/v1/reports/{uuid.uuid4()}", headers=auth_headers(user_token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REPORT_NOT_FOUND"


def test_list_reports_pagination(client, user_token, source):
    for i in range(3):
        client.post(
            "/api/v1/reports",
            json=_report_payload(source.id, text=f"Heavy rainfall flooding report number {i}"),
            headers=auth_headers(user_token),
        )

    resp = client.get("/api/v1/reports?page=1&page_size=2", headers=auth_headers(user_token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["page_size"] == 2
    assert body["pagination"]["total"] >= 3


def test_list_reports_filter_by_event_and_state(client, user_token, source):
    client.post(
        "/api/v1/reports",
        json=_report_payload(source.id, text="Severe thunderstorm warning issued", state="Kerala", city="Kochi"),
        headers=auth_headers(user_token),
    )
    client.post(
        "/api/v1/reports",
        json=_report_payload(source.id, text="Roads flooded after heavy rain", state="Karnataka"),
        headers=auth_headers(user_token),
    )

    resp = client.get(
        "/api/v1/reports?event=flood&state=karnataka", headers=auth_headers(user_token)
    )
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["event_type"] == "FLOOD"
        assert item["state"].lower() == "karnataka"
