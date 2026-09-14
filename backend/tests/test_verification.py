import uuid

from tests.conftest import auth_headers


def _create_report(client, token, source):
    resp = client.post(
        "/api/v1/reports",
        json={
            "source_id": str(source.id),
            "text": "Severe thunderstorm with high winds reported downtown",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city": "New Delhi",
            "state": "Delhi",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    return resp.json()["data"]["id"]


def test_admin_can_verify_report(client, user_token, admin_token, source):
    report_id = _create_report(client, user_token, source)

    resp = client.post(
        f"/api/v1/reports/{report_id}/verify",
        json={"reason": "Confirmed by ground team"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "VERIFIED"
    assert data["verified_by"] is not None


def test_user_cannot_verify_report(client, user_token, source):
    report_id = _create_report(client, user_token, source)

    resp = client.post(
        f"/api/v1/reports/{report_id}/verify",
        json={},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 403


def test_admin_can_reject_report(client, user_token, admin_token, source):
    report_id = _create_report(client, user_token, source)

    resp = client.post(
        f"/api/v1/reports/{report_id}/reject",
        json={"reason": "Duplicate of an already-verified report"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "REJECTED"


def test_reject_requires_a_reason(client, admin_token, user_token, source):
    report_id = _create_report(client, user_token, source)

    resp = client.post(
        f"/api/v1/reports/{report_id}/reject",
        json={"reason": ""},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 422


def test_admin_can_escalate_report(client, user_token, admin_token, source):
    report_id = _create_report(client, user_token, source)

    resp = client.post(
        f"/api/v1/reports/{report_id}/escalate",
        json={"reason": "Conflicting eyewitness accounts"},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "NEEDS_REVIEW"


def test_verify_nonexistent_report_returns_404(client, admin_token):
    resp = client.post(
        f"/api/v1/reports/{uuid.uuid4()}/verify",
        json={},
        headers=auth_headers(admin_token),
    )
    assert resp.status_code == 404


# --- Security-focused checks -----------------------------------------------


def test_password_hash_never_returned_in_login(client, normal_user):
    user, password = normal_user
    resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    body = resp.json()
    dumped = str(body)
    assert "password_hash" not in dumped
    assert password not in dumped


def test_password_hash_never_returned_in_me(client, user_token):
    resp = client.get("/api/v1/auth/me", headers=auth_headers(user_token))
    dumped = str(resp.json())
    assert "password_hash" not in dumped
    assert "$argon2" not in dumped


def test_password_hash_never_returned_in_report_verification_flow(client, user_token, admin_token, source):
    report_id = _create_report(client, user_token, source)
    resp = client.post(
        f"/api/v1/reports/{report_id}/verify", json={}, headers=auth_headers(admin_token)
    )
    assert "password" not in str(resp.json()).lower()
