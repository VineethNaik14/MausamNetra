from datetime import timedelta

from app.core.security import create_access_token

from tests.conftest import auth_headers


def test_login_success(client, normal_user):
    user, password = normal_user
    resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["user"]["email"] == user.email
    assert "password" not in body["data"]["user"]
    assert "password_hash" not in body["data"]["user"]


def test_login_wrong_password(client, normal_user):
    user, _ = normal_user
    resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": "WrongPass123!"})
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_login_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login", json={"email": "nobody@mausamnetra.dev", "password": "whatever123"}
    )
    assert resp.status_code == 401


def test_login_inactive_user(client, inactive_user):
    user, password = inactive_user
    resp = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client, normal_user, user_token):
    user, _ = normal_user
    resp = client.get("/api/v1/auth/me", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == user.email


def test_me_with_invalid_token(client):
    resp = client.get("/api/v1/auth/me", headers=auth_headers("not-a-real-token"))
    assert resp.status_code == 401


def test_me_with_expired_token(client, normal_user):
    user, _ = normal_user
    expired = create_access_token(subject=str(user.id))
    # Manually craft an already-expired token by monkeypatching exp via a
    # negative-minute token: easiest is to build one directly.
    from datetime import datetime, timezone
    from jose import jwt
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": now - timedelta(minutes=60),
        "exp": now - timedelta(minutes=30),
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert resp.status_code == 401


def test_logout(client, user_token):
    resp = client.post("/api/v1/auth/logout", headers=auth_headers(user_token))
    assert resp.status_code == 200
    assert resp.json()["success"] is True
