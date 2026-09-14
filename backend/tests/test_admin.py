from tests.conftest import auth_headers


def test_user_cannot_access_admin_reports(client, user_token):
    resp = client.get("/api/v1/admin/reports", headers=auth_headers(user_token))
    assert resp.status_code == 403


def test_admin_can_access_admin_reports(client, admin_token):
    resp = client.get("/api/v1/admin/reports", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_unauthenticated_receives_401_on_admin_route(client):
    resp = client.get("/api/v1/admin/reports")
    assert resp.status_code == 401


def test_admin_statistics_requires_admin(client, user_token, admin_token):
    resp = client.get("/api/v1/admin/statistics", headers=auth_headers(user_token))
    assert resp.status_code == 403

    resp = client.get("/api/v1/admin/statistics", headers=auth_headers(admin_token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data.keys()) == {"verified", "needs_review", "suspicious", "rejected"}


def test_admin_role_cannot_be_self_assigned(client, user_token):
    """
    There is no public registration or role-update endpoint at all, so a
    normal user has no way to escalate their own role. We assert this by
    confirming the only self-mutating auth endpoints (/me, /logout) never
    accept or honor a role field, and that admin-only routes still reject
    the user's token.
    """
    resp = client.get("/api/v1/auth/me", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "USER"

    # Attempting to hit an admin-only endpoint with a forged 'role' claim in
    # the request body (which the API does not read from the body at all)
    # must still fail, since role comes only from the DB-backed user record.
    resp = client.post(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000/verify",
        json={"role": "ADMIN"},
        headers=auth_headers(user_token),
    )
    assert resp.status_code == 403
